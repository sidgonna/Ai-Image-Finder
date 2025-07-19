#!/usr/bin/env python3
"""
AI Image Finder - Complete Single-File Application
Deployment-ready image search with AI semantic understanding
"""

import os
import sys
import pickle
import glob
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
import traceback

# Check and install requirements
def ensure_packages():
    """Ensure all required packages are installed"""
    required_packages = [
        ('PyQt5', 'PyQt5'),
        ('sentence_transformers', 'sentence-transformers'), 
        ('faiss', 'faiss-cpu'),
        ('PIL', 'Pillow'),
        ('numpy', 'numpy'),
        ('torch', 'torch'),
        ('tqdm', 'tqdm')
    ]
    
    missing = []
    for import_name, pip_name in required_packages:
        try:
            if import_name == 'faiss':
                import faiss
            elif import_name == 'PIL':
                from PIL import Image
            else:
                __import__(import_name)
        except ImportError:
            missing.append(pip_name)
    
    if missing:
        print(f"📦 Installing required packages: {', '.join(missing)}")
        for package in missing:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print("✅ All packages installed successfully!")

# Ensure packages are available
try:
    ensure_packages()
except Exception as e:
    print(f"❌ Failed to install packages: {e}")
    sys.exit(1)

# Now import everything
import faiss
import torch
import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# Configuration
SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp']
AI_MODEL = "clip-ViT-B-32"
EXCLUDED_FOLDERS = ['System32', 'Windows', 'Program Files', 'AppData', '.git', '__pycache__', 'temp', 'tmp', 'cache']
MIN_FILE_SIZE_KB = 1
MAX_FILE_SIZE_MB = 50

class ImageIndexer(QObject):
    """Image indexer with progress signals for GUI"""
    progress_signal = pyqtSignal(str, int)  # message, percentage
    finished_signal = pyqtSignal(bool, str, int)  # success, message, image_count
    
    def __init__(self):
        super().__init__()
        self.model = None
        self.index = None
        self.image_paths = []
        self.failed_images = []
        self.should_stop = False
    
    def stop_indexing(self):
        self.should_stop = True
    
    def _should_exclude_folder(self, folder_path: str) -> bool:
        folder_name = os.path.basename(folder_path).lower()
        return any(excluded.lower() in folder_name for excluded in EXCLUDED_FOLDERS)
    
    def _is_valid_image_file(self, file_path: str) -> bool:
        _, ext = os.path.splitext(file_path.lower())
        if ext not in [e.lower() for e in SUPPORTED_EXTENSIONS]:
            return False
        
        try:
            file_size_kb = os.path.getsize(file_path) / 1024
            return MIN_FILE_SIZE_KB <= file_size_kb <= (MAX_FILE_SIZE_MB * 1024)
        except OSError:
            return False
    
    def _get_all_drives(self) -> List[str]:
        """Get all available drives on the system"""
        drives = []
        if sys.platform == "win32":
            # Windows - check all drive letters
            for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                drive = f'{letter}:\\'
                if os.path.exists(drive):
                    drives.append(drive)
        else:
            # Unix-like systems
            drives = ['/']
            # Add common mount points
            mount_points = ['/media', '/mnt', '/Volumes']  # Linux, macOS
            for mount in mount_points:
                if os.path.exists(mount):
                    try:
                        for item in os.listdir(mount):
                            full_path = os.path.join(mount, item)
                            if os.path.isdir(full_path):
                                drives.append(full_path)
                    except PermissionError:
                        continue
        return drives
    
    def index_images(self, scan_whole_machine: bool = False, specific_folder: str = None):
        """Index images with progress reporting"""
        try:
            self.progress_signal.emit("🤖 Loading AI model...", 5)
            self.model = SentenceTransformer(AI_MODEL)
            dimension = self.model.get_sentence_embedding_dimension() or 512
            self.index = faiss.IndexFlatL2(int(dimension))
            self.image_paths = []
            self.failed_images = []
            
            if scan_whole_machine:
                self.progress_signal.emit("🔍 Scanning all drives and connected devices...", 10)
                scan_locations = self._get_all_drives()
            else:
                scan_locations = [specific_folder]
            
            # Collect all images
            all_images = []
            total_folders = 0
            
            self.progress_signal.emit("📂 Finding images...", 15)
            for location in scan_locations:
                if self.should_stop:
                    return
                    
                if not os.path.exists(location):
                    continue
                    
                for dirpath, dirnames, filenames in os.walk(location):
                    if self.should_stop:
                        return
                        
                    total_folders += 1
                    
                    # Skip excluded folders
                    if self._should_exclude_folder(dirpath):
                        dirnames.clear()
                        continue
                    
                    for filename in filenames:
                        if self.should_stop:
                            return
                            
                        file_path = os.path.join(dirpath, filename)
                        if self._is_valid_image_file(file_path):
                            all_images.append(file_path)
                    
                    # Update progress periodically
                    if total_folders % 100 == 0:
                        self.progress_signal.emit(f"📂 Scanned {total_folders} folders, found {len(all_images)} images...", 
                                                min(40, 15 + (total_folders // 100)))
            
            if not all_images:
                self.finished_signal.emit(False, "No images found to index!", 0)
                return
            
            # Remove duplicates while preserving order
            unique_images = list(dict.fromkeys(all_images))
            
            self.progress_signal.emit(f"🚀 Processing {len(unique_images)} unique images...", 45)
            
            # Process images
            embeddings_list = []
            processed_count = 0
            
            for i, img_path in enumerate(unique_images):
                if self.should_stop:
                    return
                
                try:
                    image = Image.open(img_path).convert('RGB')
                    if image.size[0] > 1024 or image.size[1] > 1024:
                        image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                    
                    embeddings = self.model.encode([image], batch_size=1, convert_to_numpy=True)
                    if len(embeddings) > 0:
                        embeddings_list.append(embeddings[0])
                        self.image_paths.append(img_path)
                        processed_count += 1
                
                except Exception as e:
                    self.failed_images.append((img_path, str(e)))
                
                # Update progress
                progress = 45 + int((i / len(unique_images)) * 40)
                if i % 10 == 0 or i == len(unique_images) - 1:
                    self.progress_signal.emit(f"📊 Processed {processed_count}/{len(unique_images)} images...", progress)
            
            if not embeddings_list:
                self.finished_signal.emit(False, "No images could be processed!", 0)
                return
            
            self.progress_signal.emit("💾 Building search index...", 90)
            embeddings_array = np.array(embeddings_list).astype('float32')
            self.index.add(embeddings_array)
            
            # Save index
            self.progress_signal.emit("💾 Saving index files...", 95)
            os.makedirs("data", exist_ok=True)
            faiss.write_index(self.index, "data/faiss_index.bin")
            with open("data/image_paths.pkl", 'wb') as f:
                pickle.dump(self.image_paths, f)
            
            self.finished_signal.emit(True, f"✅ Successfully indexed {processed_count} images!", processed_count)
            
        except Exception as e:
            self.finished_signal.emit(False, f"❌ Indexing failed: {str(e)}", 0)

class ImageSearcher:
    """Image searcher for finding similar images"""
    def __init__(self, index_path: str, paths_path: str):
        self.model = SentenceTransformer(AI_MODEL)
        self.index = faiss.read_index(index_path)
        with open(paths_path, 'rb') as f:
            self.image_paths = pickle.load(f)

    def search(self, query_image: str, k: int = None) -> List[Tuple[str, float]]:
        if k is None:
            k = len(self.image_paths)  # Return all results by default
        
        image = Image.open(query_image).convert('RGB')
        query_embedding = self.model.encode([image], batch_size=1, convert_to_numpy=True)
        
        distances, indices = self.index.search(query_embedding.astype('float32'), min(k, len(self.image_paths)))
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.image_paths):
                results.append((self.image_paths[idx], float(distance)))
        
        return results

class ImageResultWidget(QFrame):
    """Widget to display individual image results"""
    def __init__(self, image_path: str, similarity_score: float):
        super().__init__()
        self.image_path = image_path
        self.similarity_score = similarity_score
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setFixedSize(140, 140)
        self.image_label.setStyleSheet("border: 2px solid #ddd; border-radius: 8px;")
        self.image_label.setAlignment(Qt.AlignCenter)
        
        try:
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(136, 136, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("No Preview")
        except:
            self.image_label.setText("No Preview")
        
        # Filename
        filename = os.path.basename(self.image_path)
        if len(filename) > 18:
            filename = filename[:15] + "..."
        
        self.filename_label = QLabel(filename)
        self.filename_label.setAlignment(Qt.AlignCenter)
        self.filename_label.setStyleSheet("font-weight: bold; color: #333; font-size: 11px;")
        
        # Similarity score
        self.score_label = QLabel(f"Similarity: {self.similarity_score:.1f}%")
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setStyleSheet("color: #666; font-size: 10px;")
        
        layout.addWidget(self.image_label)
        layout.addWidget(self.filename_label)
        layout.addWidget(self.score_label)
        
        self.setLayout(layout)
        self.setToolTip(f"Path: {self.image_path}\nSimilarity: {self.similarity_score:.1f}%")
        self.setStyleSheet("ImageResultWidget:hover { background-color: #f0f0f0; border-radius: 8px; }")
    
    def mousePressEvent(self, event):
        """Handle click to open image location"""
        try:
            if sys.platform == "win32":
                os.startfile(os.path.dirname(self.image_path))
            elif sys.platform == "darwin":
                subprocess.run(["open", os.path.dirname(self.image_path)])
            else:
                subprocess.run(["xdg-open", os.path.dirname(self.image_path)])
        except:
            pass

class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎯 AI Image Finder - Semantic Search")
        self.setGeometry(100, 100, 1400, 900)
        self.searcher = None
        self.indexer = None
        self.indexing_thread = None
        
        self.setStyleSheet("""
            QMainWindow { background-color: #f8f9fa; }
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #ddd; 
                border-radius: 8px; 
                margin-top: 10px; 
                padding-top: 10px;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 10px; 
                padding: 0 5px 0 5px; 
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #0056b3; }
            QPushButton:pressed { background-color: #004085; }
            QPushButton:disabled { background-color: #6c757d; }
        """)
        
        self.init_ui()
        self.load_index()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        
        # Left panel
        left_panel = self.create_left_panel()
        left_panel.setFixedWidth(350)
        
        # Right panel
        right_panel = self.create_right_panel()
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)
        
        central_widget.setLayout(main_layout)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
    
    def create_left_panel(self):
        """Create the left control panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Status area
        status_group = QGroupBox("🎯 AI Image Finder")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Ready to search! 🚀\n\nDrag & drop an image here\nor use the browse button below.")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 3px dashed #007bff;
                border-radius: 12px;
                padding: 20px;
                font-size: 14px;
                color: #495057;
            }
        """)
        self.status_label.setMinimumHeight(120)
        status_layout.addWidget(self.status_label)
        
        # Browse button
        self.browse_btn = QPushButton("📁 Browse for Image")
        self.browse_btn.clicked.connect(self.browse_image)
        status_layout.addWidget(self.browse_btn)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Indexing options
        index_group = QGroupBox("🔧 Indexing Options")
        index_layout = QVBoxLayout()
        
        # Index type selection
        self.whole_machine_radio = QRadioButton("🌐 Scan whole machine + connected devices")
        self.whole_machine_radio.setToolTip("Scan all drives including USB, network drives, etc.\n(May take 1-2 hours for large collections)")
        
        self.specific_folder_radio = QRadioButton("📁 Scan specific folder only")
        self.specific_folder_radio.setChecked(True)
        self.specific_folder_radio.setToolTip("Faster option - scan only a chosen folder")
        
        index_layout.addWidget(self.whole_machine_radio)
        index_layout.addWidget(self.specific_folder_radio)
        
        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select folder to index...")
        self.folder_browse_btn = QPushButton("📂")
        self.folder_browse_btn.clicked.connect(self.browse_folder)
        self.folder_browse_btn.setFixedWidth(40)
        
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.folder_browse_btn)
        index_layout.addLayout(folder_layout)
        
        # Auto-detect button
        self.auto_detect_btn = QPushButton("🔍 Auto-detect image folders")
        self.auto_detect_btn.clicked.connect(self.auto_detect_folders)
        index_layout.addWidget(self.auto_detect_btn)
        
        # Start indexing button
        self.index_btn = QPushButton("🚀 Start Indexing")
        self.index_btn.clicked.connect(self.start_indexing)
        index_layout.addWidget(self.index_btn)
        
        # Stop indexing button
        self.stop_btn = QPushButton("⏹️ Stop Indexing")
        self.stop_btn.clicked.connect(self.stop_indexing)
        self.stop_btn.setVisible(False)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #dc3545; }")
        index_layout.addWidget(self.stop_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        index_layout.addWidget(self.progress_bar)
        
        # Progress text
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        self.progress_label.setStyleSheet("font-size: 11px; color: #666;")
        index_layout.addWidget(self.progress_label)
        
        index_group.setLayout(index_layout)
        layout.addWidget(index_group)
        
        # Index info
        info_group = QGroupBox("📊 Index Information")
        info_layout = QVBoxLayout()
        
        self.index_info_label = QLabel("No index loaded")
        info_layout.addWidget(self.index_info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self):
        """Create the right results panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Results header
        self.results_header = QLabel("🎯 Search Results")
        self.results_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; margin: 10px;")
        layout.addWidget(self.results_header)
        
        # Results scroll area
        self.results_scroll = QScrollArea()
        self.results_widget = QWidget()
        self.results_layout = QGridLayout()
        self.results_layout.setSpacing(10)
        self.results_widget.setLayout(self.results_layout)
        self.results_scroll.setWidget(self.results_widget)
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setStyleSheet("""
            QScrollArea { 
                background-color: white; 
                border: 2px solid #dee2e6; 
                border-radius: 8px;
            }
        """)
        
        layout.addWidget(self.results_scroll)
        panel.setLayout(layout)
        return panel
    
    def load_index(self):
        """Load existing search index if available"""
        index_path = "data/faiss_index.bin"
        paths_path = "data/image_paths.pkl"
        
        if os.path.exists(index_path) and os.path.exists(paths_path):
            try:
                self.searcher = ImageSearcher(index_path, paths_path)
                
                # Show index statistics
                with open(paths_path, 'rb') as f:
                    image_paths = pickle.load(f)
                
                index_size_mb = os.path.getsize(index_path) / 1024 / 1024
                self.index_info_label.setText(f"✅ Index loaded\n📊 {len(image_paths):,} images indexed\n💾 Index size: {index_size_mb:.1f} MB")
                self.status_label.setText("✅ Ready to search!\n\n📸 Drag & drop an image\nto find similar ones")
                
            except Exception as e:
                self.index_info_label.setText(f"❌ Error loading index:\n{str(e)}")
                self.status_label.setText("⚠️ Index error!\n\nPlease re-index your images")
        else:
            self.index_info_label.setText("❌ No index found\n\n🔄 Please index images first")
            self.status_label.setText("⚠️ No search index found!\n\nPlease index your images\nusing the options below")
    
    def auto_detect_folders(self):
        """Auto-detect common image folders"""
        locations = [
            os.path.expanduser('~/Pictures'),
            os.path.expanduser('~/Desktop'),
            os.path.expanduser('~/Downloads'),
            'D:/Pictures',
            'E:/Pictures'
        ]
        
        found_folders = []
        for location in locations:
            if os.path.exists(location):
                # Quick check for images
                for ext in ['.jpg', '.png', '.jpeg']:
                    if glob.glob(os.path.join(location, f'*{ext}'), recursive=True):
                        found_folders.append(location)
                        break
        
        if found_folders:
            # Show selection dialog
            folder, ok = QInputDialog.getItem(
                self, "Select Folder", 
                "Found these image folders:", 
                found_folders, 0, False
            )
            if ok:
                self.folder_input.setText(folder)
        else:
            QMessageBox.information(self, "No Folders Found", "No image folders found automatically.\nPlease select a folder manually.")
    
    def browse_folder(self):
        """Browse for folder to index"""
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            self.folder_input.setText(folder)
    
    def browse_image(self):
        """Browse for image to search"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image to Search", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp);;All Files (*)"
        )
        if file_path:
            self.search_image(file_path)
    
    def start_indexing(self):
        """Start the indexing process"""
        if self.whole_machine_radio.isChecked():
            scan_whole_machine = True
            specific_folder = None
        else:
            scan_whole_machine = False
            specific_folder = self.folder_input.text().strip()
            
            if not specific_folder:
                QMessageBox.warning(self, "No Folder Selected", "Please select a folder to index!")
                return
            
            if not os.path.exists(specific_folder):
                QMessageBox.warning(self, "Folder Not Found", "Selected folder doesn't exist!")
                return
        
        # Confirm with user
        if scan_whole_machine:
            reply = QMessageBox.question(
                self, "Confirm Full Scan",
                "🌐 Scan entire machine including connected drives?\n\n"
                "⏰ This may take 1-2 hours for large collections\n"
                "💾 Will scan all drives (C:, D:, USB, network, etc.)\n"
                "🔍 More comprehensive but slower\n\n"
                "Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        # Start indexing in thread
        self.indexing_thread = QThread()
        self.indexer = ImageIndexer()
        self.indexer.moveToThread(self.indexing_thread)
        
        # Connect signals
        self.indexer.progress_signal.connect(self.update_progress)
        self.indexer.finished_signal.connect(self.indexing_finished)
        self.indexing_thread.started.connect(
            lambda: self.indexer.index_images(scan_whole_machine, specific_folder)
        )
        
        # Update UI
        self.index_btn.setVisible(False)
        self.stop_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start thread
        self.indexing_thread.start()
    
    def stop_indexing(self):
        """Stop the indexing process"""
        if self.indexer:
            self.indexer.stop_indexing()
        self.indexing_finished(False, "Indexing stopped by user", 0)
    
    def update_progress(self, message: str, percentage: int):
        """Update indexing progress"""
        self.progress_label.setText(message)
        self.progress_bar.setValue(percentage)
        QApplication.processEvents()
    
    def indexing_finished(self, success: bool, message: str, image_count: int):
        """Handle indexing completion"""
        # Clean up thread
        if self.indexing_thread and self.indexing_thread.isRunning():
            self.indexing_thread.quit()
            self.indexing_thread.wait()
        
        # Update UI
        self.index_btn.setVisible(True)
        self.stop_btn.setVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Indexing Complete", f"✅ {message}\n\n🎯 You can now search for similar images!")
            self.load_index()  # Reload index
        else:
            QMessageBox.warning(self, "Indexing Failed", f"❌ {message}")
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path) and any(file_path.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                self.search_image(file_path)
                break
    
    def search_image(self, image_path: str):
        """Search for similar images"""
        if not self.searcher:
            QMessageBox.warning(self, "No Index", "⚠️ No search index loaded!\nPlease index your images first.")
            return
        
        try:
            self.status_label.setText(f"🔍 Searching...\n\n📸 Query: {os.path.basename(image_path)}")
            QApplication.processEvents()
            
            # Perform search (get all results, no duplication)
            results = self.searcher.search(image_path)
            
            # Remove the query image from results if it exists
            query_image_abs = os.path.abspath(image_path)
            filtered_results = []
            for path, distance in results:
                if os.path.abspath(path) != query_image_abs:
                    filtered_results.append((path, distance))
            
            if not filtered_results:
                self.status_label.setText("❌ No similar images found!\n\nTry with a different image\nor re-index more images.")
                self.results_header.setText("🎯 No Results Found")
                self.clear_results()
                return
            
            # Display results
            self.display_results(filtered_results, image_path)
            
            # Update status
            self.status_label.setText(f"✅ Search complete!\n\n📊 Found {len(filtered_results)} similar images")
            self.results_header.setText(f"🎯 Similar Images ({len(filtered_results)} found)")
            
        except Exception as e:
            error_msg = f"❌ Search failed!\n\nError: {str(e)}"
            self.status_label.setText(error_msg)
            QMessageBox.critical(self, "Search Error", f"Search failed:\n\n{str(e)}")
    
    def clear_results(self):
        """Clear previous results"""
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def display_results(self, results: List[Tuple[str, float]], query_image_path: str):
        """Display search results dynamically"""
        self.clear_results()
        
        try:
            # Calculate columns based on window width
            cols = max(1, (self.results_scroll.width() - 50) // 160)  # 160px per image
            
            # Convert distances to similarity percentages
            if results:
                max_distance = max([r[1] for r in results])
                min_distance = min([r[1] for r in results])
                distance_range = max_distance - min_distance
            
            for idx, (result_path, distance) in enumerate(results):
                row = idx // cols
                col = idx % cols
                
                # Calculate similarity (higher = more similar)
                if distance_range == 0:
                    similarity = 100.0
                else:
                    similarity = max(0, 100 - ((distance - min_distance) / distance_range * 100))
                
                # Create result widget
                result_widget = ImageResultWidget(result_path, similarity)
                self.results_layout.addWidget(result_widget, row, col)
            
            # Add stretch to fill remaining space
            if results:
                last_row = (len(results) - 1) // cols + 1
                self.results_layout.setRowStretch(last_row, 1)
            
        except Exception as e:
            print(f"Error displaying results: {e}")

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("AI Image Finder")
    app.setOrganizationName("AI Tools")
    
    try:
        window = MainWindow()
        window.show()
        
        print("✅ AI Image Finder launched successfully!")
        print("💡 Drag & drop images to find similar ones!")
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
