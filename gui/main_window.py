import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QListWidget, QListWidgetItem, QHBoxLayout, QProgressBar, QApplication
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt
from engine.searcher import ImageSearcher

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Semantic Image Search Engine")
        self.setGeometry(100, 100, 900, 600)
        self.searcher = None
        self.init_ui()
        self.load_index()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        self.info_label = QLabel("Drag and drop an image here or click + to select an image.")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("+")
        self.add_btn.clicked.connect(self.open_file_dialog)
        btn_layout.addWidget(self.add_btn)
        layout.addLayout(btn_layout)

        self.result_list = QListWidget()
        layout.addWidget(self.result_list)

        central_widget.setLayout(layout)

        # Enable drag and drop
        self.setAcceptDrops(True)

    def load_index(self):
        index_path = os.path.join("data", "faiss_index.bin")
        paths_path = os.path.join("data", "image_paths.pkl")
        if os.path.exists(index_path) and os.path.exists(paths_path):
            self.searcher = ImageSearcher(index_path, paths_path)
        else:
            self.info_label.setText("Index not found. Please run the indexer first.")

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            self.search_image(file_path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.search_image(file_path)
                break

    def search_image(self, image_path):
        if not self.searcher:
            self.info_label.setText("Index not loaded.")
            return
        self.info_label.setText(f"Searching for similar images to: {image_path}")
        QApplication.processEvents()
        try:
            results = self.searcher.search(image_path, k=10)
        except Exception as e:
            self.info_label.setText(f"Error: {str(e)}")
            return
        self.result_list.clear()
        for path, distance in results:
            item = QListWidgetItem(f"{os.path.basename(path)} (distance: {distance:.2f})")
            item.setToolTip(path)
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                icon = QIcon(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                item.setIcon(icon)
            self.result_list.addItem(item)
        self.info_label.setText("Search complete. Hover over results to see full path.")
