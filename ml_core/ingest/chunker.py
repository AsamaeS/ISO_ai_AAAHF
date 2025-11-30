"""
Intelligent Chunking System

Chunks ISO documents respecting section boundaries with metadata preservation.
Splits large sections into overlapping sub-chunks for better retrieval.
"""

import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import tiktoken  # For accurate token counting

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Container for text chunk with metadata."""
    chunk_id: str
    text: str
    section_id: str
    section_name: str
    page_start: int
    page_end: int
    token_count: int
    document: str
    chunk_index: int = 0  # Index within section if split
    total_chunks_in_section: int = 1


class DocumentChunker:
    """
    Intelligent chunking that respects ISO document structure.
    
    Strategy:
    1. Primary: Chunk by ISO section (if size is reasonable)
    2. Secondary: Split large sections into 350-450 token sub-chunks
    3. Preserve metadata for each chunk
    """
    
    def __init__(
        self,
        target_tokens: int = 400,
        min_tokens: int = 200,
        max_tokens: int = 600,
        overlap_tokens: int = 50,
        encoding_name: str = "cl100k_base"  # GPT-4 tokenizer
    ):
        """
        Initialize chunker.
        
        Args:
            target_tokens: Target chunk size
            min_tokens: Minimum chunk size
            max_tokens: Maximum chunk size (split if exceeds)
            overlap_tokens: Overlap for split chunks
            encoding_name: Tokenizer encoding to use
        """
        self.target_tokens = target_tokens
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        
        # Initialize tokenizer
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Failed to load tiktoken encoding: {e}. Using simple word count.")
            self.encoding = None
    
    def chunk_sections(
        self,
        sections: List[Dict],
        document_name: str
    ) -> List[Chunk]:
        """
        Chunk ISO sections into retrievable units.
        
        Args:
            sections: List of section dicts from parse_sections
            document_name: Name of source document
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        for section in sections:
            section_chunks = self._chunk_single_section(section, document_name)
            chunks.extend(section_chunks)
        
        logger.info(f"Created {len(chunks)} chunks from {len(sections)} sections")
        return chunks
    
    def _chunk_single_section(self, section: Dict, document_name: str) -> List[Chunk]:
        """
        Chunk a single section, splitting if necessary.
        
        Args:
            section: Section dictionary
            document_name: Document name
            
        Returns:
            List of chunks (1 if small, multiple if split)
        """
        text = section['text']
        token_count = self.count_tokens(text)
        
        # If section is within limits, keep as single chunk
        if token_count <= self.max_tokens:
            chunk_id = self._generate_chunk_id(
                document_name, 
                section['section_id'],
                0
            )
            
            return [Chunk(
                chunk_id=chunk_id,
                text=text,
                section_id=section['section_id'],
                section_name=section['section_name'],
                page_start=section['page_start'],
                page_end=section['page_end'],
                token_count=token_count,
                document=document_name,
                chunk_index=0,
                total_chunks_in_section=1
            )]
        
        # Section is too large, split into sub-chunks
        logger.info(f"Splitting large section {section['section_id']} "
                   f"({token_count} tokens) into sub-chunks")
        
        return self._split_long_section(section, document_name)
    
    def _split_long_section(self, section: Dict, document_name: str) -> List[Chunk]:
        """
        Split a long section into overlapping sub-chunks.
        
        Args:
            section: Section dictionary
            document_name: Document name
            
        Returns:
            List of sub-chunks
        """
        text = section['text']
        chunks = []
        
        # Split by sentences for clean boundaries
        sentences = self._split_into_sentences(text)
        
        current_chunk_text = []
        current_tokens = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            # If adding this sentence exceeds max, save current chunk
            if current_tokens + sentence_tokens > self.target_tokens and current_chunk_text:
                # Save chunk
                chunk_text = ' '.join(current_chunk_text)
                chunk_id = self._generate_chunk_id(
                    document_name,
                    section['section_id'],
                    chunk_index
                )
                
                chunks.append(Chunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    section_id=section['section_id'],
                    section_name=section['section_name'],
                    page_start=section['page_start'],
                    page_end=section['page_end'],
                    token_count=current_tokens,
                    document=document_name,
                    chunk_index=chunk_index
                ))
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(
                    current_chunk_text,
                    self.overlap_tokens
                )
                current_chunk_text = overlap_text
                current_tokens = self.count_tokens(' '.join(current_chunk_text))
                chunk_index += 1
            
            # Add sentence to current chunk
            current_chunk_text.append(sentence)
            current_tokens += sentence_tokens
        
        # Save final chunk
        if current_chunk_text:
            chunk_text = ' '.join(current_chunk_text)
            chunk_id = self._generate_chunk_id(
                document_name,
                section['section_id'],
                chunk_index
            )
            
            chunks.append(Chunk(
                chunk_id=chunk_id,
                text=chunk_text,
                section_id=section['section_id'],
                section_name=section['section_name'],
                page_start=section['page_start'],
                page_end=section['page_end'],
                token_count=current_tokens,
                document=document_name,
                chunk_index=chunk_index
            ))
        
        # Update total chunks count
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk.total_chunks_in_section = total_chunks
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting (could be improved with NLP library)
        # Split on . ! ? followed by space and capital letter
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-Ÿ])', text)
        
        # Clean up
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _get_overlap_text(self, sentences: List[str], overlap_tokens: int) -> List[str]:
        """
        Get last N tokens worth of sentences for overlap.
        
        Args:
            sentences: List of sentences
            overlap_tokens: Target overlap size
            
        Returns:
            List of sentences for overlap
        """
        overlap = []
        tokens = 0
        
        # Work backwards from end
        for sentence in reversed(sentences):
            sentence_tokens = self.count_tokens(sentence)
            if tokens + sentence_tokens <= overlap_tokens:
                overlap.insert(0, sentence)
                tokens += sentence_tokens
            else:
                break
        
        return overlap
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count
            
        Returns:
            Token count
        """
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback: rough estimate (1 token ≈ 0.75 words)
            words = len(text.split())
            return int(words * 1.33)
    
    def _generate_chunk_id(
        self,
        document_name: str,
        section_id: str,
        chunk_index: int
    ) -> str:
        """
        Generate unique chunk ID.
        
        Args:
            document_name: Document name
            section_id: Section ID
            chunk_index: Chunk index within section
            
        Returns:
            Unique chunk ID
        """
        # Sanitize document name
        doc_clean = re.sub(r'[^\w\-]', '_', document_name.lower())
        section_clean = section_id.replace('.', '_')
        
        return f"{doc_clean}_{section_clean}_chunk_{chunk_index}"


def chunk_document(
    sections: List[Dict],
    document_name: str,
    target_tokens: int = 400
) -> List[Dict]:
    """
    Convenience function to chunk a document.
    
    Args:
        sections: List of sections from parse_sections
        document_name: Name of document
        target_tokens: Target chunk size
        
    Returns:
        List of chunk dictionaries
    """
    chunker = DocumentChunker(target_tokens=target_tokens)
    chunks = chunker.chunk_sections(sections, document_name)
    
    # Convert to dicts
    return [
        {
            'chunk_id': c.chunk_id,
            'text': c.text,
            'section_id': c.section_id,
            'section_name': c.section_name,
            'page_start': c.page_start,
            'page_end': c.page_end,
            'token_count': c.token_count,
            'document': c.document,
            'chunk_index': c.chunk_index,
            'total_chunks_in_section': c.total_chunks_in_section
        }
        for c in chunks
    ]


if __name__ == "__main__":
    # Example usage
    sample_sections = [
        {
            'section_id': '4.1',
            'section_name': 'Compréhension de l\'organisme',
            'text': 'This is a short section with minimal text.',
            'page_start': 5,
            'page_end': 5,
            'level': 2,
            'parent_id': '4'
        },
        {
            'section_id': '4.1.2',
            'section_name': 'Champ d\'application',
            'text': ' '.join(['This is a very long section. ' * 100]),  # Long text
            'page_start': 6,
            'page_end': 8,
            'level': 3,
            'parent_id': '4.1'
        }
    ]
    
    chunks = chunk_document(sample_sections, "ISO 9001")
    
    print(f"Created {len(chunks)} chunks:\n")
    for chunk in chunks:
        print(f"Chunk: {chunk['chunk_id']}")
        print(f"  Section: {chunk['section_id']} - {chunk['section_name']}")
        print(f"  Tokens: {chunk['token_count']}")
        print(f"  Part {chunk['chunk_index'] + 1}/{chunk['total_chunks_in_section']}")
        print(f"  Page: {chunk['page_start']}-{chunk['page_end']}")
        print()
