"""
Semantic Search Module

Performs semantic search using FAISS index with metadata enrichment.
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path

try:
    import faiss
except ImportError:
    raise ImportError("FAISS required. Install: pip install faiss-cpu")

from .embedder import Embedder, load_embedder
from .build_faiss import FAISSIndexBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticSearch:
    """
    Semantic search engine using embeddings and FAISS.
    
    Features:
    - Top-k retrieval
    - Metadata enrichment
    - Score normalization
    - Result ranking
    """
    
    def __init__(
        self,
        index: faiss.Index,
        metadata: Dict,
        embedder: Embedder
    ):
        """
        Initialize search engine.
        
        Args:
            index: FAISS index
            metadata: ID to metadata mapping
            embedder: Embedder instance
        """
        self.index = index
        self.metadata = metadata
        self.embedder = embedder
        
        logger.info("Semantic search engine initialized")
        logger.info(f"  Index size: {self.index.ntotal} vectors")
        logger.info(f"  Embedding dim: {self.embedder.embedding_dim}")
    
    def search(
        self,
        query: str,
        k: int = 5,
        min_score: Optional[float] = None
    ) -> List[Dict]:
        """
        Search for relevant chunks.
        
        Args:
            query: Search query
            k: Number of results to return
            min_score: Minimum similarity score (optional)
            
        Returns:
            List of result dictionaries with metadata and scores
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Reshape for FAISS
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        
        # Search index
        distances, indices = self.index.search(query_embedding, k)
        
        # Build results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx == -1:  # FAISS returns -1 for insufficient results
                continue
            
            # Get metadata
            chunk_metadata = self.metadata[int(idx)]
            
            # Convert distance to similarity score
            # For L2: lower is better, convert to similarity
            # For cosine (inner product): higher is better
            score = self._distance_to_score(distance)
            
            # Filter by minimum score if specified
            if min_score is not None and score < min_score:
                continue
            
            result = {
                'chunk_id': chunk_metadata['chunk_id'],
                'text': chunk_metadata['text'],
                'section': chunk_metadata['section_id'],
                'section_name': chunk_metadata['section_name'],
                'page': chunk_metadata['page_start'],
                'document': chunk_metadata['document'],
                'score': float(score),
                'distance': float(distance)
            }
            
            results.append(result)
        
        logger.info(f"Found {len(results)} results for query: '{query[:50]}...'")
        
        return results
    
    def _distance_to_score(self, distance: float) -> float:
        """
        Convert FAISS distance to normalized similarity score.
        
        Args:
            distance: FAISS distance
            
        Returns:
            Similarity score (0-1, higher is better)
        """
        # For Inner Product (cosine with normalized vectors): 
        # distance is already similarity
        # For L2: use exponential decay
        
        # Check index type
        if isinstance(self.index, (faiss.IndexFlatIP, faiss.IndexHNSWFlat)):
            # Inner product - distance is similarity
            return max(0.0, min(1.0, distance))
        else:
            # L2 distance - convert to similarity
            # Use exponential decay: exp(-distance^2)
            return float(np.exp(-distance ** 2))
    
    def batch_search(
        self,
        queries: List[str],
        k: int = 5
    ) -> List[List[Dict]]:
        """
        Search multiple queries at once.
        
        Args:
            queries: List of queries
            k: Results per query
            
        Returns:
            List of result lists
        """
        all_results = []
        
        for query in queries:
            results = self.search(query, k=k)
            all_results.append(results)
        
        return all_results
    
    def search_by_chunk_id(self, chunk_id: str) -> Optional[Dict]:
        """
        Retrieve metadata by chunk ID.
        
        Args:
            chunk_id: Chunk ID to find
            
        Returns:
            Chunk metadata or None
        """
        for idx, meta in self.metadata.items():
            if meta['chunk_id'] == chunk_id:
                return meta
        return None
    
    def get_similar_chunks(
        self,
        chunk_id: str,
        k: int = 5
    ) -> List[Dict]:
        """
        Find similar chunks to a given chunk.
        
        Args:
            chunk_id: Reference chunk ID
            k: Number of similar chunks to return
            
        Returns:
            List of similar chunks
        """
        # Find chunk index
        chunk_idx = None
        for idx, meta in self.metadata.items():
            if meta['chunk_id'] == chunk_id:
                chunk_idx = idx
                break
        
        if chunk_idx is None:
            logger.warning(f"Chunk not found: {chunk_id}")
            return []
        
        # Get embedding
        embedding = self.index.reconstruct(chunk_idx).reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(embedding, k + 1)  # +1 to exclude self
        
        # Build results (skip first result which is the chunk itself)
        results = []
        for idx, distance in zip(indices[0][1:], distances[0][1:]):
            if idx == -1:
                continue
            
            chunk_metadata = self.metadata[int(idx)]
            score = self._distance_to_score(distance)
            
            results.append({
                'chunk_id': chunk_metadata['chunk_id'],
                'text': chunk_metadata['text'],
                'section': chunk_metadata['section_id'],
                'section_name': chunk_metadata['section_name'],
                'page': chunk_metadata['page_start'],
                'document': chunk_metadata['document'],
                'score': float(score)
            })
        
        return results


def load_search_engine(
    index_dir: str,
    index_name: str = "faiss_index",
    embedder_model: str = "BAAI/bge-small-en-v1.5"
) -> SemanticSearch:
    """
    Load search engine from saved index.
    
    Args:
        index_dir: Directory containing index
        index_name: Index file basename
        embedder_model: Embedder model to use
        
    Returns:
        SemanticSearch instance
    """
    # Load index
    builder = FAISSIndexBuilder()
    index, metadata = builder.load_index(index_dir, index_name)
    
    # Load embedder
    embedder = load_embedder(embedder_model)
    
    # Create search engine
    return SemanticSearch(index, metadata, embedder)


if __name__ == "__main__":
    # Example usage
    print("To test search, first build an index using build_faiss.py")
    print("\nExample:")
    print("  from ml_core.embeddings.search import load_search_engine")
    print("  search = load_search_engine('./output')")
    print("  results = search.search('What is ISO 9001?', k=5)")
    print("  for r in results:")
    print("    print(f\"[{r['score']:.3f}] {r['section']} - {r['text'][:100]}\")")
