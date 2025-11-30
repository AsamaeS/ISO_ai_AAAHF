"""
Complete Ingestion Pipeline

Orchestrates PDF → Text → Sections → Chunks → Embeddings workflow.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .document_extractor import extract_document, MultiFormatExtractor
from .clean_text import clean_iso_text
from .parse_sections import parse_sections
from .chunker import chunk_document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Complete document ingestion pipeline.
    
    Workflow:
    PDF → Extract Text → Clean → Parse Sections → Chunk → Save
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize pipeline.
        
        Args:
            config: Optional configuration dict
        """
        self.config = config or {}
        
        # Default configuration
        self.use_paddleocr = self.config.get('use_paddleocr', True)
        self.target_tokens = self.config.get('target_tokens', 400)
        self.min_chars_threshold = self.config.get('min_chars_threshold', 100)
    
    def ingest_document(
        self,
        document_path: str,
        document_name: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> Dict:
        """
        Complete ingestion pipeline for any supported document format.
        
        Supports: PDF, Word (.docx, .doc), Excel (.xlsx, .xls)
        
        Args:
            document_path: Path to document file
            document_name: Name for the document (defaults to filename)
            output_dir: Directory to save outputs (optional)
            
        Returns:
            Dictionary with chunks and statistics
        """
        document_path = Path(document_path)
        
        if not document_path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        # Default document name
        if not document_name:
            document_name = document_path.stem
        
        logger.info(f"Starting ingestion pipeline for: {document_name}")
        logger.info(f"=" * 60)
        
        # Step 1: Extract text from document (auto-detects format)
        logger.info("Step 1/4: Extracting text from document...")
        extraction_result = extract_document(str(document_path))
        
        raw_text = extraction_result.text
        logger.info(f"  ✓ Extracted {extraction_result.total_chars} characters "
                   f"from {extraction_result.total_pages} pages/sheets")
        logger.info(f"  ✓ File type: {extraction_result.file_type.upper()}")
        logger.info(f"  ✓ Method: {extraction_result.extraction_method}")
        
        # Step 2: Clean text
        logger.info("Step 2/4: Cleaning text...")
        cleaned_text = clean_iso_text(raw_text)
        logger.info(f"  ✓ Text cleaned ({len(cleaned_text)} characters after cleaning)")
        
        # Step 3: Parse sections
        logger.info("Step 3/4: Parsing ISO sections...")
        
        # Prepare page info for section parser
        page_info = [
            {
                'page_number': p['page_number'],
                'char_count': p['char_count']
            }
            for p in extraction_result.pages
        ]
        
        sections = parse_sections(cleaned_text, page_info)
        logger.info(f"  ✓ Parsed {len(sections)} sections")
        
        # Step 4: Create chunks
        logger.info("Step 4/4: Chunking sections...")
        chunks = chunk_document(
            sections,
            document_name,
            target_tokens=self.target_tokens
        )
        logger.info(f"  ✓ Created {len(chunks)} chunks")
        
        # Calculate statistics
        stats = self._calculate_stats(
            extraction_result,
            sections,
            chunks
        )
        
        logger.info(f"=" * 60)
        logger.info("Ingestion complete!")
        logger.info(f"  Total chunks: {stats['total_chunks']}")
        logger.info(f"  Avg tokens/chunk: {stats['avg_tokens_per_chunk']:.1f}")
        logger.info(f"  Total sections: {stats['total_sections']}")
        
        # Save outputs if directory specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save chunks
            chunks_file = output_path / f"{document_name}_chunks.json"
            self.save_chunks(chunks, str(chunks_file))
            logger.info(f"  Saved chunks to: {chunks_file}")
            
            # Save metadata
            metadata = {
                'document_name': document_name,
                'source_file': str(document_path),
                'file_type': extraction_result.file_type,
                'ingestion_date': datetime.now().isoformat(),
                'statistics': stats,
                'config': self.config
            }
            metadata_file = output_path / f"{document_name}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"  Saved metadata to: {metadata_file}")
        
        return {
            'chunks': chunks,
            'sections': sections,
            'statistics': stats,
            'document_name': document_name
        }
    
    def _calculate_stats(
        self,
        extraction_result: Dict,
        sections: List[Dict],
        chunks: List[Dict]
    ) -> Dict:
        """Calculate pipeline statistics."""
        total_tokens = sum(c['token_count'] for c in chunks)
        avg_tokens = total_tokens / len(chunks) if chunks else 0
        
        # Section level distribution
        section_levels = {}
        for section in sections:
            level = section['level']
            section_levels[level] = section_levels.get(level, 0) + 1
        
        return {
            'total_pages': extraction_result.total_pages,
            'total_chars': extraction_result.total_chars,
            'extraction_method': extraction_result.extraction_method,
            'file_type': extraction_result.file_type,
            'total_sections': len(sections),
            'section_levels': section_levels,
            'total_chunks': len(chunks),
            'total_tokens': total_tokens,
            'avg_tokens_per_chunk': avg_tokens,
            'min_tokens': min(c['token_count'] for c in chunks) if chunks else 0,
            'max_tokens': max(c['token_count'] for c in chunks) if chunks else 0
        }
    
    def save_chunks(self, chunks: List[Dict], output_path: str):
        """
        Save chunks to JSON file.
        
        Args:
            chunks: List of chunk dictionaries
            output_path: Output file path
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved {len(chunks)} chunks to {output_path}")
    
    def load_chunks(self, input_path: str) -> List[Dict]:
        """
        Load chunks from JSON file.
        
        Args:
            input_path: Input file path
            
        Returns:
            List of chunk dictionaries
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        logger.debug(f"Loaded {len(chunks)} chunks from {input_path}")
        return chunks


def ingest_document(
    document_path: str,
    document_name: Optional[str] = None,
    output_dir: Optional[str] = None,
    config: Optional[Dict] = None
) -> Dict:
    """
    Convenience function to ingest a document (PDF, Word, or Excel).
    
    Args:
        document_path: Path to document file
        document_name: Name for document
        output_dir: Output directory
        config: Configuration dict
        
    Returns:
        Ingestion results
    """
    pipeline = IngestionPipeline(config)
    return pipeline.ingest_document(document_path, document_name, output_dir)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        output_directory = sys.argv[2] if len(sys.argv) > 2 else "./output"
        
        # Run pipeline
        result = ingest_document(
            pdf_file,
            output_dir=output_directory
        )
        
        print("\n" + "=" * 60)
        print("INGESTION SUMMARY")
        print("=" * 60)
        print(f"Document: {result['document_name']}")
        print(f"Chunks created: {len(result['chunks'])}")
        print(f"Sections parsed: {len(result['sections'])}")
        print("\nTop 3 sections:")
        for i, section in enumerate(result['sections'][:3]):
            print(f"  {i+1}. {section['section_id']} - {section['section_name']}")
    else:
        print("Usage: python ingest_pipeline.py <pdf_file> [output_dir]")
