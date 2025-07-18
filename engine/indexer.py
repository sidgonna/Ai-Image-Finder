import os
import pickle
from typing import List, Tuple
import faiss
import torch
from PIL import Image
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import numpy as np

class ImageIndexer:
    def __init__(self, model_name: str = "clip-ViT-B-32"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(int(self.dimension))
        self.image_paths = []

    def _process_image(self, image_path: str) -> np.ndarray:
        try:
            image = Image.open(image_path).convert('RGB')
            # For sentence-transformers >=2.2.0, use as_tensor=False for numpy output
            embeddings = self.model.encode([image], batch_size=1, as_tensor=False)
            return embeddings[0]
        except Exception as e:
            print(f"Error processing image {image_path}: {str(e)}")
            return None

    def build_index(self, root_dir: str) -> None:
        """Build the FAISS index from images in the given directory."""
        # Collect all image paths
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        all_images = []
        
        print("Collecting image paths...")
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if os.path.splitext(filename)[1].lower() in valid_extensions:
                    all_images.append(os.path.join(dirpath, filename))

        print(f"Found {len(all_images)} images. Processing...")
        embeddings_list = []

        # Process images with progress bar
        for img_path in tqdm(all_images, desc="Processing images"):
            embedding = self._process_image(img_path)
            if embedding is not None:
                embeddings_list.append(embedding)
                self.image_paths.append(img_path)

        if not embeddings_list:
            raise ValueError("No valid images found to process")

        # Convert to numpy array and add to index
        embeddings_array = np.array(embeddings_list).astype('float32')
        self.index.add(embeddings_array)

    def save(self, index_path: str, paths_path: str) -> None:
        """Save the FAISS index and image paths to disk."""
        faiss.write_index(self.index, index_path)
        with open(paths_path, 'wb') as f:
            pickle.dump(self.image_paths, f)

def main(image_dir: str, output_dir: str = "data"):
    """Main function to build and save the index."""
    indexer = ImageIndexer()
    
    print(f"Building index from images in: {image_dir}")
    indexer.build_index(image_dir)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the index and paths
    index_path = os.path.join(output_dir, "faiss_index.bin")
    paths_path = os.path.join(output_dir, "image_paths.pkl")
    
    print(f"Saving index to: {index_path}")
    indexer.save(index_path, paths_path)
    print("Indexing complete!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build image search index")
    parser.add_argument("--path", required=True, help="Path to directory containing images")
    parser.add_argument("--output", default="data", help="Output directory for index files")
    args = parser.parse_args()
    
    main(args.path, args.output)
