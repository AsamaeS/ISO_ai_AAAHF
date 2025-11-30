"""
Batch Document Processor

Process allfiles in a directory (PDF, Word, Excel).
"""

import logging
from pathlib import Path
from typing import List, Dict
import json

from .ingest_pipeline import IngestionPipeline
from ..embeddings.embedder import Embedder
from ..embeddings.build_faiss import build_index_from_chunks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_directory(
    input_dir: str,
    output_dir: str = "./data/chunks",
    index_dir: str = "./data/index",
    file_patterns: List[str] = None
) -> Dict:
    """
    Process all documents in a directory.
    
    Args:
        input_dir: Directory containing documents
        output_dir: Output directory for chunks
        index_dir: Output directory for FAISS index
        file_patterns: File patterns to process (default: all supported)
        
    Returns:
        Processing statistics
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Directory not found: {input_dir}")
    
    # Default patterns
    if file_patterns is None:
        file_patterns = ['*.pdf', '*.docx', '*.doc', '*.xlsx', '*.xls']
    
    # Find all matching files
    all_files = []
    for pattern in file_patterns:
        all_files.extend(input_path.rglob(pattern))
    
    logger.info(f"Found {len(all_files)} documents to process")
    
    # Initialize pipeline
    pipeline = IngestionPipeline()
    
    # Process each file
    all_chunks = []
    processed = 0
    failed = 0
    
    for file_path in all_files:
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {file_path.name}")
            logger.info(f"{'='*60}")
            
            result = pipeline.ingest_document(
                str(file_path),
                document_name=file_path.stem,
                output_dir=output_dir
            )
            
            all_chunks.extend(result['chunks'])
            processed += 1
            
        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            failed += 1
    
    logger.info(f"\n{'='*60}")
    logger.info("Batch processing complete!")
    logger.info(f"  Processed: {processed}/{len(all_files)}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Total chunks: {len(all_chunks)}")
    logger.info(f"{'='*60}")
    
    # Save combined chunks
    combined_file = Path(output_dir) / "all_documents_chunks.json"
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved combined chunks to: {combined_file}")
    
    # Build FAISS index
    if all_chunks:
        logger.info("\nBuilding FAISS index from all chunks...")
        
        embedder = Embedder()
        texts = [chunk['text'] for chunk in all_chunks]
        embeddings = embedder.embed_texts(texts, show_progress=True)
        
        build_index_from_chunks(all_chunks, embeddings, index_dir)
        
        logger.info(f"FAISS index saved to: {index_dir}")
    
    return {
        'total_files': len(all_files),
        'processed': processed,
        'failed': failed,
        'total_chunks': len(all_chunks),
        'output_dir': output_dir,
        'index_dir': index_dir
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        input_directory = sys.argv[1]
        output_directory = sys.argv[2] if len(sys.argv) > 2 else "./data/chunks"
        index_directory = sys.argv[3] if len(sys.argv) > 3 else "./data/index"
        
        result = process_directory(
            input_directory,
            output_directory,
            index_directory
        )
        
        print("\n" + "=" * 60)
        print("BATCH PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total files: {result['total_files']}")
        print(f"Successfully processed: {result['processed']}")
        print(f"Failed: {result['failed']}")
        print(f"Total chunks: {result['total_chunks']}")
        print(f"\nOutputs:")
        print(f"  Chunks: {result['output_dir']}")
        print(f"  Index: {result['index_dir']}")
        print("=" * 60)
    else:
        print("Usage: python batch_processor.py <input_directory> [output_dir] [index_dir]")
        print("\nExample:")
        print("  python batch_processor.py ./data/pdfs ./data/chunks ./data/index")
