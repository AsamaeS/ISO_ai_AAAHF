"""
FAISS Index Builder

Creates and manages FAISS indices for efficient vector search.
"""

import logging
import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

try:
    import faiss
except ImportError:
    raise ImportError("FAISS required. Install: pip install faiss-cpu")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FAISSIndexBuilder:
    """
    FAISS index builder and manager.
    
    Supports:
    - IndexFlatL2: Exact search (good for small datasets)
    - IndexHNSWFlat: Approximate search (faster for large datasets)
    """
    
    def __init__(self, index_type: str = "flat", metric: str = "l2"):
        """
        Initialize index builder.
        
        Args:
            index_type: Type of index ("flat" or "hnsw")
            metric: Distance metric ("l2" or "cosine")
        """
        self.index_type = index_type.lower()
        self.metric = metric.lower()
        
        if self.index_type not in ["flat", "hnsw"]:
            raise ValueError(f"Invalid index type: {index_type}. Use 'flat' or 'hnsw'")
        
        if self.metric not in ["l2", "cosine"]:
            raise ValueError(f"Invalid metric: {metric}. Use 'l2' or 'cosine'")
    
    def build_index(
        self,
        embeddings: np.ndarray,
        metadata: List[Dict],
        hnsw_m: int = 32,
        hnsw_ef_construction: int = 200
    ) -> Tuple[faiss.Index, Dict]:
        """
        Build FAISS index from embeddings.
        
        Args:
            embeddings: Embeddings array (n_docs, dim)
            metadata: Metadata for each embedding
            hnsw_m: Number of connections for HNSW (ignored for flat)
            hnsw_ef_construction: Construction parameter for HNSW
            
        Returns:
            Tuple of (FAISS index, metadata mapping dict)
        """
        if len(embeddings) != len(metadata):
            raise ValueError("Number of embeddings must match metadata count")
        
        n_docs, dim = embeddings.shape
        
        logger.info(f"Building {self.index_type.upper()} index...")
        logger.info(f"  Documents: {n_docs}")
        logger.info(f"  Embedding dim: {dim}")
        logger.info(f"  Metric: {self.metric}")
        
        # Create index based on type
        if self.index_type == "flat":
            # Exact search
            if self.metric == "l2":
                index = faiss.IndexFlatL2(dim)
            else:  # cosine
                index = faiss.IndexFlatIP(dim)  # Inner product for normalized vectors
        
        elif self.index_type == "hnsw":
            # HNSW approximate search
            if self.metric == "l2":
                index = faiss.IndexHNSWFlat(dim, hnsw_m)
            else:  # cosine
                index = faiss.IndexHNSWFlat(dim, hnsw_m, faiss.METRIC_INNER_PRODUCT)
            
            index.hnsw.efConstruction = hnsw_ef_construction
            logger.info(f"  HNSW M: {hnsw_m}")
            logger.info(f"  HNSW efConstruction: {hnsw_ef_construction}")
        
        # Add embeddings to index
        embeddings = embeddings.astype('float32')
        index.add(embeddings)
        
        logger.info(f"Index built successfully with {index.ntotal} vectors")
        
        # Create ID to metadata mapping
        id_to_metadata = {
            i: metadata[i]
            for i in range(len(metadata))
        }
        
        return index, id_to_metadata
    
    def save_index(
        self,
        index: faiss.Index,
        metadata: Dict,
        output_dir: str,
        index_name: str = "faiss_index"
    ):
        """
        Save FAISS index and metadata to disk.
        
        Args:
            index: FAISS index
            metadata: Metadata dictionary
            output_dir: Output directory
            index_name: Base name for files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_file = output_path / f"{index_name}.bin"
        faiss.write_index(index, str(index_file))
        logger.info(f"Saved FAISS index to: {index_file}")
        
        # Save metadata as JSON
        metadata_file = output_path / f"{index_name}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved metadata to: {metadata_file}")
        
        # Save index config
        config = {
            'index_type': self.index_type,
            'metric': self.metric,
            'n_vectors': index.ntotal,
            'dimension': index.d
        }
        config_file = output_path / f"{index_name}_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved config to: {config_file}")
    
    def load_index(
        self,
        index_dir: str,
        index_name: str = "faiss_index"
    ) -> Tuple[faiss.Index, Dict]:
        """
        Load FAISS index and metadata from disk.
        
        Args:
            index_dir: Directory containing index files
            index_name: Base name of index files
            
        Returns:
            Tuple of (FAISS index, metadata dict)
        """
        index_dir = Path(index_dir)
        
        # Load FAISS index
        index_file = index_dir / f"{index_name}.bin"
        if not index_file.exists():
            raise FileNotFoundError(f"Index file not found: {index_file}")
        
        index = faiss.read_index(str(index_file))
        logger.info(f"Loaded FAISS index from: {index_file}")
        logger.info(f"  Vectors: {index.ntotal}")
        logger.info(f"  Dimension: {index.d}")
        
        # Load metadata
        metadata_file = index_dir / f"{index_name}_metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Convert string keys back to integers
        metadata = {int(k): v for k, v in metadata.items()}
        
        logger.info(f"Loaded metadata for {len(metadata)} vectors")
        
        return index, metadata


def build_index_from_chunks(
    chunks: List[Dict],
    embeddings: np.ndarray,
    output_dir: str,
    index_type: str = "flat",
    index_name: str = "faiss_index"
) -> Tuple[faiss.Index, Dict]:
    """
    Convenience function to build index from chunks.
    
    Args:
        chunks: List of chunk dictionaries
        embeddings: Embeddings array
        output_dir: Output directory
        index_type: Type of FAISS index
        index_name: Name for index files
        
    Returns:
        Tuple of (index, metadata)
    """
    # Prepare metadata from chunks
    metadata = []
    for chunk in chunks:
        metadata.append({
            'chunk_id': chunk['chunk_id'],
            'text': chunk['text'],
            'section_id': chunk['section_id'],
            'section_name': chunk['section_name'],
            'page_start': chunk['page_start'],
            'page_end': chunk['page_end'],
            'document': chunk['document'],
            'token_count': chunk['token_count']
        })
    
    # Build index
    builder = FAISSIndexBuilder(index_type=index_type)
    index, id_to_metadata = builder.build_index(embeddings, metadata)
    
    # Save index
    builder.save_index(index, id_to_metadata, output_dir, index_name)
    
    return index, id_to_metadata


if __name__ == "__main__":
    # Example usage
    print("Testing FAISS index builder...")
    
    # Create sample embeddings
    n_docs = 100
    dim = 384
    embeddings = np.random.randn(n_docs, dim).astype('float32')
    
    # Normalize for cosine similarity
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    # Create sample metadata
    metadata = [
        {
            'chunk_id': f'chunk_{i}',
            'text': f'Sample text for chunk {i}',
            'section_id': f'{i // 10}.{i % 10}',
            'document': 'ISO 9001'
        }
        for i in range(n_docs)
    ]
    
    # Build index
    builder = FAISSIndexBuilder(index_type="flat", metric="cosine")
    index, id_to_metadata = builder.build_index(embeddings, metadata)
    
    # Test search
    query_embedding = np.random.randn(dim).astype('float32')
    query_embedding = query_embedding / np.linalg.norm(query_embedding)
    
    k = 5
    distances, indices = index.search(query_embedding.reshape(1, -1), k)
    
    print(f"\nTop {k} results:")
    for i, (idx, dist) in enumerate(zip(indices[0], distances[0])):
        print(f"  {i+1}. Document {idx}: distance={dist:.4f}")
        print(f"     Metadata: {id_to_metadata[idx]}")
