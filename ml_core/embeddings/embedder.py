"""
Embeddings Module

Generates semantic embeddings using BAAI/bge-small-en-v1.5.
Optimized for CPU execution with batch processing.
"""

import logging
import numpy as np
from typing import List, Union, Optional
import torch

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError("sentence-transformers required. Install: pip install sentence-transformers")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Embedder:
    """
    Semantic embeddings generator using BAAI/bge-small-en-v1.5.
    
    Model features:
    - 384-dimensional embeddings
    - Optimized for semantic search
    - Fast inference (suitable for CPU)
    - Strong performance on English text
    """
    
    DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: Optional[str] = None,
        batch_size: int = 32
    ):
        """
        Initialize embedder.
        
        Args:
            model_name: HuggingFace model name
            device: Device to use ('cpu', 'cuda', None=auto)
            batch_size: Batch size for processing
        """
        self.model_name = model_name
        self.batch_size = batch_size
        
        # Determine device (CPU only for Intel GPU compatibility)
        if device is None:
            # Force CPU for Intel GPU systems
            self.device = 'cpu'
            logger.info("Using CPU for embeddings (Intel GPU detected)")
        else:
            self.device = device
        
        logger.info(f"Loading embedding model: {model_name}")
        
        # Load model
        self.model = SentenceTransformer(
            model_name,
            device=self.device
        )
        
        # Get embedding dimension
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"Model loaded successfully")
        logger.info(f"  Embedding dimension: {self.embedding_dim}")
        logger.info(f"  Device: {self.device}")
    
    def embed_texts(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        show_progress: bool = False,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of text strings
            batch_size: Batch size (uses default if None)
            show_progress: Show progress bar
            normalize: L2 normalize embeddings
            
        Returns:
            numpy array of shape (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([])
        
        batch_size = batch_size or self.batch_size
        
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        
        # Generate embeddings
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=normalize
        )
        
        logger.info(f"Generated embeddings shape: {embeddings.shape}")
        
        return embeddings
    
    def embed_query(
        self,
        query: str,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate embedding for a single query.
        
        For BGE models, queries should be prefixed with "Represent this sentence for searching relevant passages:"
        But sentence-transformers handles this automatically.
        
        Args:
            query: Query string
            normalize: L2 normalize embedding
            
        Returns:
            numpy array of shape (embedding_dim,)
        """
        embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=normalize
        )[0]
        
        return embedding
    
    def compute_similarity(
        self,
        embed1: np.ndarray,
        embed2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embed1: First embedding
            embed2: Second embedding
            
        Returns:
            Similarity score (0-1)
        """
        # Embeddings should already be normalized
        similarity = np.dot(embed1, embed2)
        return float(similarity)
    
    def compute_similarities(
        self,
        query_embedding: np.ndarray,
        corpus_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute similarities between query and corpus.
        
        Args:
            query_embedding: Query embedding (embedding_dim,)
            corpus_embeddings: Corpus embeddings (n_docs, embedding_dim)
            
        Returns:
            Similarity scores (n_docs,)
        """
        # Matrix multiplication for batch similarity
        similarities = np.dot(corpus_embeddings, query_embedding)
        return similarities


def load_embedder(
    model_name: str = "BAAI/bge-small-en-v1.5",
    device: Optional[str] = None
) -> Embedder:
    """
    Convenience function to load embedder.
    
    Args:
        model_name: Model to load
        device: Device to use
        
    Returns:
        Embedder instance
    """
    return Embedder(model_name=model_name, device=device)


def embed_texts(
    texts: List[str],
    model_name: str = "BAAI/bge-small-en-v1.5",
    batch_size: int = 32
) -> np.ndarray:
    """
    Quick function to embed texts.
    
    Args:
        texts: Texts to embed
        model_name: Model to use
        batch_size: Batch size
        
    Returns:
        Embeddings array
    """
    embedder = Embedder(model_name=model_name, batch_size=batch_size)
    return embedder.embed_texts(texts)


if __name__ == "__main__":
    # Example usage
    print("Testing embedder...")
    
    # Sample texts
    texts = [
        "The organization shall determine external and internal issues.",
        "L'organisme doit déterminer les enjeux externes et internes.",
        "What is the scope of ISO 9001?",
        "Quality management system requirements."
    ]
    
    # Load embedder
    embedder = load_embedder()
    
    # Generate embeddings
    embeddings = embedder.embed_texts(texts, show_progress=True)
    
    print(f"\nEmbeddings shape: {embeddings.shape}")
    print(f"Embedding dimension: {embedder.embedding_dim}")
    
    # Test similarity
    query = "What are the external issues?"
    query_emb = embedder.embed_query(query)
    
    similarities = embedder.compute_similarities(query_emb, embeddings)
    
    print(f"\nQuery: '{query}'")
    print("\nSimilarities:")
    for i, (text, sim) in enumerate(zip(texts, similarities)):
        print(f"  {i+1}. [{sim:.3f}] {text[:60]}...")
