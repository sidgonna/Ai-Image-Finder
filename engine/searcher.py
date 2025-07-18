import pickle
from typing import List, Tuple
import faiss
import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer

class ImageSearcher:
    def __init__(self, index_path: str, paths_path: str, model_name: str = "clip-ViT-B-32"):
        # Load the CLIP model
        self.model = SentenceTransformer(model_name)
        
        # Load the FAISS index
        self.index = faiss.read_index(index_path)
        
        # Load the image paths
        with open(paths_path, 'rb') as f:
            self.image_paths = pickle.load(f)

    def search(self, query_image: str, k: int = 10) -> List[Tuple[str, float]]:
        """
        Search for similar images to the query image.
        
        Args:
            query_image: Path to the query image
            k: Number of results to return
            
        Returns:
            List of tuples containing (image_path, distance)
        """
        # Process the query image
        try:
            image = Image.open(query_image).convert('RGB')
            query_embedding = self.model.encode([image], batch_size=1, convert_to_numpy=True)
        except Exception as e:
            raise ValueError(f"Error processing query image: {str(e)}")

        # Search the index
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Return results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.image_paths):  # Ensure valid index
                results.append((self.image_paths[idx], float(distance)))
        
        return results
