"""
Unit and Integration Tests for RAG Pipeline

Tests cover:
- Text cleaning
- Section parsing
- Chunking logic
- Embeddings generation
- FAISS search
- End-to-end RAG (with mock data)
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import json

# Import modules to test
from ml_core.ingest.clean_text import TextCleaner, clean_text
from ml_core.ingest.parse_sections import ISOSectionParser, parse_sections
from ml_core.ingest.chunker import DocumentChunker, chunk_document
from ml_core.embeddings.embedder import Embedder
from ml_core.embeddings.build_faiss import FAISSIndexBuilder


class TestTextCleaning:
    """Test text cleaning functionality."""
    
    def test_page_number_removal(self):
        """Test page number patterns are removed."""
        cleaner = TextCleaner()
        
        text = """Page 1/30
        
Some important text here.

Page 2/30

More text here."""
        
        cleaned = cleaner.clean_text(text)
        
        # Page numbers should be removed
        assert "Page 1/30" not in cleaned
        assert "Page 2/30" not in cleaned
        assert "Some important text here" in cleaned
        assert "More text here" in cleaned
    
    def test_unicode_normalization(self):
        """Test unicode normalization."""
        cleaner = TextCleaner()
        
        # Text with special unicode
        text = "Café résumé naïve"
        cleaned = cleaner.clean_text(text)
        
        # Should be normalized
        assert len(cleaned) > 0
        assert "Caf" in cleaned or "Café" in cleaned
    
    def test_whitespace_normalization(self):
        """Test whitespace handling."""
        cleaner = TextCleaner()
        
        text = "Multiple    spaces   here.\n\n\n\nMultiple newlines."
        cleaned = cleaner.clean_text(text)
        
        # Multiple spaces should be normalized
        assert "    " not in cleaned
        # Should have at most double newlines
        assert "\n\n\n" not in cleaned


class TestSectionParsing:
    """Test ISO section parsing."""
    
    def test_section_detection(self):
        """Test section header detection."""
        parser = ISOSectionParser()
        
        text = """
4 Contexte de l'organisme

Some text here.

4.1 Compréhension de l'organisme

More text.

4.1.2 Champ d'application

Even more text.
"""
        
        sections = parser.parse_sections(text)
        
        # Should find 3 sections
        assert len(sections) == 3
        
        # Check section IDs
        section_ids = [s.section_id for s in sections]
        assert "4" in section_ids
        assert "4.1" in section_ids
        assert "4.1.2" in section_ids
    
    def test_section_hierarchy(self):
        """Test section hierarchy levels."""
        parser = ISOSectionParser()
        
        text = """
4 Top Level

4.1 Second Level

4.1.2 Third Level
"""
        
        sections = parser.parse_sections(text)
        
        # Check levels
        for section in sections:
            if section.section_id == "4":
                assert section.level == 1
            elif section.section_id == "4.1":
                assert section.level == 2
                assert section.parent_id == "4"
            elif section.section_id == "4.1.2":
                assert section.level == 3
                assert section.parent_id == "4.1"


class TestChunking:
    """Test chunking functionality."""
    
    def test_small_section_chunking(self):
        """Test that small sections stay as single chunks."""
        chunker = DocumentChunker(target_tokens=400, max_tokens=600)
        
        sections = [
            {
                'section_id': '4.1',
                'section_name': 'Test Section',
                'text': 'This is a small section with minimal text.',
                'page_start': 1,
                'page_end': 1,
                'level': 2,
                'parent_id': '4'
            }
        ]
        
        chunks = chunker.chunk_sections(sections, "Test Doc")
        
        # Should create 1 chunk
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0
        assert chunks[0].total_chunks_in_section == 1
    
    def test_large_section_splitting(self):
        """Test that large sections are split."""
        chunker = DocumentChunker(target_tokens=100, max_tokens=150)
        
        # Create a large section
        long_text = "This is a sentence. " * 100  # Repeat 100 times
        
        sections = [
            {
                'section_id': '4.1',
                'section_name': 'Large Section',
                'text': long_text,
                'page_start': 1,
                'page_end': 3,
                'level': 2,
                'parent_id': '4'
            }
        ]
        
        chunks = chunker.chunk_sections(sections, "Test Doc")
        
        # Should create multiple chunks
        assert len(chunks) > 1
        
        # Check chunk IDs are unique
        chunk_ids = [c.chunk_id for c in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))
    
    def test_chunk_metadata(self):
        """Test chunk metadata preservation."""
        chunker = DocumentChunker()
        
        sections = [
            {
                'section_id': '4.1.2',
                'section_name': 'Application Scope',
                'text': 'Some text about scope.',
                'page_start': 5,
                'page_end': 6,
                'level': 3,
                'parent_id': '4.1'
            }
        ]
        
        chunks = chunker.chunk_sections(sections, "ISO 9001")
        
        chunk = chunks[0]
        assert chunk.section_id == '4.1.2'
        assert chunk.section_name == 'Application Scope'
        assert chunk.page_start == 5
        assert chunk.document == "ISO 9001"


class TestEmbeddings:
    """Test embedding generation."""
    
    @pytest.fixture
    def embedder(self):
        """Create embedder instance."""
        # Use small model for testing
        return Embedder(model_name="BAAI/bge-small-en-v1.5", device="cpu")
    
    def test_single_embedding(self, embedder):
        """Test single text embedding."""
        text = "This is a test sentence."
        embedding = embedder.embed_query(text)
        
        # Check shape
        assert embedding.shape == (embedder.embedding_dim,)
        assert embedder.embedding_dim == 384  # bge-small dimension
    
    def test_batch_embeddings(self, embedder):
        """Test batch embedding."""
        texts = [
            "First sentence.",
            "Second sentence.",
            "Third sentence."
        ]
        
        embeddings = embedder.embed_texts(texts)
        
        # Check shape
        assert embeddings.shape == (3, embedder.embedding_dim)
    
    def test_similarity_computation(self, embedder):
        """Test similarity between embeddings."""
        text1 = "The organization shall determine external issues."
        text2 = "External issues must be determined by the organization."
        text3 = "Completely different topic about cats."
        
        emb1 = embedder.embed_query(text1)
        emb2 = embedder.embed_query(text2)
        emb3 = embedder.embed_query(text3)
        
        sim_12 = embedder.compute_similarity(emb1, emb2)
        sim_13 = embedder.compute_similarity(emb1, emb3)
        
        # Similar sentences should have higher similarity
        assert sim_12 > sim_13


class TestFAISSIndex:
    """Test FAISS index building and search."""
    
    def test_index_creation(self):
        """Test FAISS index creation."""
        # Create sample embeddings
        n_docs = 10
        dim = 384
        embeddings = np.random.randn(n_docs, dim).astype('float32')
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Create metadata
        metadata = [
            {
                'chunk_id': f'chunk_{i}',
                'text': f'Text {i}',
                'section_id': f'{i}',
                'section_name': f'Section {i}',
                'page_start': i,
                'page_end': i,
                'document': 'Test Doc',
                'token_count': 100
            }
            for i in range(n_docs)
        ]
        
        # Build index
        builder = FAISSIndexBuilder(index_type="flat", metric="cosine")
        index, id_to_metadata = builder.build_index(embeddings, metadata)
        
        # Check index
        assert index.ntotal == n_docs
        assert len(id_to_metadata) == n_docs
    
    def test_index_search(self):
        """Test FAISS search."""
        # Create sample embeddings
        n_docs = 20
        dim = 384
        embeddings = np.random.randn(n_docs, dim).astype('float32')
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        metadata = [{'chunk_id': f'chunk_{i}', 'text': f'Text {i}'} for i in range(n_docs)]
        
        # Build index
        builder = FAISSIndexBuilder(index_type="flat", metric="cosine")
        index, _ = builder.build_index(embeddings, metadata)
        
        # Search
        query = embeddings[0].reshape(1, -1)  # Use first embedding as query
        k = 5
        distances, indices = index.search(query, k)
        
        # Check results
        assert len(indices[0]) == k
        assert indices[0][0] == 0  # First result should be the query itself
    
    def test_index_save_load(self):
        """Test saving and loading index."""
        # Create sample data
        n_docs = 10
        dim = 384
        embeddings = np.random.randn(n_docs, dim).astype('float32')
        metadata = [{'chunk_id': f'chunk_{i}'} for i in range(n_docs)]
        
        # Build index
        builder = FAISSIndexBuilder()
        index, id_to_metadata = builder.build_index(embeddings, metadata)
        
        # Save to temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            builder.save_index(index, id_to_metadata, tmpdir, "test_index")
            
            # Load index
            loaded_index, loaded_metadata = builder.load_index(tmpdir, "test_index")
            
            # Check loaded index
            assert loaded_index.ntotal == index.ntotal
            assert len(loaded_metadata) == len(id_to_metadata)


class TestEndToEndRAG:
    """Integration test for complete RAG pipeline (with mocks)."""
    
    def test_complete_pipeline_flow(self):
        """Test the complete flow (without actual LLM inference)."""
        # 1. Create mock document
        sample_text = """
4 Context of the Organization

The organization shall determine external and internal issues.

4.1 Understanding the Organization

The organization shall monitor and review information about these external and internal issues.

4.1.2 Scope

The organization shall determine the boundaries and applicability of the quality management system.
"""
        
        # 2. Clean text
        cleaned = clean_text(sample_text)
        assert len(cleaned) > 0
        
        # 3. Parse sections
        sections = parse_sections(cleaned)
        assert len(sections) > 0
        
        # 4. Chunk sections
        chunks = chunk_document(sections, "ISO 9001 Test")
        assert len(chunks) > 0
        
        # 5. Each chunk should have required fields
        for chunk in chunks:
            assert 'chunk_id' in chunk
            assert 'text' in chunk
            assert 'section_id' in chunk
            assert 'document' in chunk
        
        print(f"✓ Complete pipeline test passed: {len(chunks)} chunks created")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
