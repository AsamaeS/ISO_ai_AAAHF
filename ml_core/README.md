# 🚀 ML Core - RAG Pipeline for ISO Documents

Complete machine learning pipeline for processing ISO documents with semantic search and question answering.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Technical Choices](#technical-choices)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This project implements a **production-ready RAG (Retrieval-Augmented Generation) pipeline** for ISO document navigation. It combines:

- **Data Engineering**: PDF extraction → Text cleaning → Section parsing → Intelligent chunking
- **Machine Learning**: Semantic embeddings with BAAI/bge-small-en-v1.5
- **Vector Search**: Efficient FAISS indexing
- **Generation**: LLaMA 3.2 3B Instruct with 4-bit quantization
- **MLOps**: REST API, Docker deployment, comprehensive testing

**Optimized for**: 8GB RAM systems with CPU-only execution (Intel GPU compatible)

---

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  PDF Docs   │────▶│   Ingestion  │────▶│  Embeddings │────▶│ FAISS Index  │
└─────────────┘     │   Pipeline   │     │   (BAAI)    │     └──────────────┘
                    └──────────────┘     └─────────────┘            │
                           │                                        │
                           ▼                                        ▼
                    ┌──────────────┐                        ┌──────────────┐
                    │    Chunks    │                        │    Search    │
                    │   + Metadata │                        │    Engine    │
                    └──────────────┘                        └──────────────┘
                                                                    │
                                                                    ▼
                    ┌──────────────┐                        ┌──────────────┐
                    │     LLaMA    │◀───────────────────────│  RAG Pipeline│
                    │  3.2 3B 4bit │                        └──────────────┘
                    └──────────────┘                                │
                           │                                        │
                           ▼                                        ▼
                    ┌──────────────────────────────────────────────────────┐
                    │                   FastAPI REST API                   │
                    └──────────────────────────────────────────────────────┘
```

---

## ✨ Features

### Data Ingestion
- ✅ PDF text extraction (text-based + OCR for scanned pages)
- ✅ Tesseract + PaddleOCR support
- ✅ Professional text cleaning (page numbers, headers, footers)
- ✅ ISO section parsing with regex (4, 4.1, 4.1.2, etc.)
- ✅ Intelligent chunking (350-450 tokens, respects sections)

### Embeddings & Search
- ✅ BAAI/bge-small-en-v1.5 (384-dim, CPU-optimized)
- ✅ FAISS vector search (exact and approximate)
- ✅ Metadata enrichment (section, page, document)
- ✅ Similarity scoring

### RAG System
- ✅ LLaMA 3.2 3B Instruct (4-bit quantized for 8GB RAM)
- ✅ Context-based answer generation
- ✅ Source citation with section references
- ✅ Customizable prompt templates

### API & Deployment
- ✅ FastAPI REST API
- ✅ `/ask` - Question answering
- ✅ `/ingest` - Document ingestion
- ✅ `/info` - System status
- ✅ Docker containerization
- ✅ YAML configuration

---

## 📦 Installation

### Prerequisites

- Python 3.10+
- 8GB RAM minimum
- Tesseract OCR (optional but recommended)

### Local Installation

```bash
# Clone repository
cd iso-doc-navigator-main/ml_core

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Tesseract (optional)
# Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-fra
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract tesseract-lang
```

### Docker Installation

```bash
# Build image
docker build -t ml-core-rag .

# Run container
docker run -p 8000:8000 \
  -v ./data:/data \
  -v ./models:/models \
  ml-core-rag
```

---

## 🚀 Quick Start

### Step 1: Ingest a PDF

```python
from ml_core.ingest.ingest_pipeline import ingest_document

# Process PDF
result = ingest_document(
    pdf_path="./data/pdfs/ISO_9001.pdf",
    document_name="ISO 9001",
    output_dir="./data/chunks"
)

print(f"Created {len(result['chunks'])} chunks")
```

### Step 2: Build FAISS Index

```python
from ml_core.embeddings.embedder import Embedder
from ml_core.embeddings.build_faiss import build_index_from_chunks
import json

# Load chunks
with open("./data/chunks/ISO_9001_chunks.json") as f:
    chunks = json.load(f)

# Generate embeddings
embedder = Embedder()
texts = [c['text'] for c in chunks]
embeddings = embedder.embed_texts(texts, show_progress=True)

# Build index
build_index_from_chunks(
    chunks,
    embeddings,
    output_dir="./data/index"
)
```

### Step 3: Ask Questions

```python
from ml_core.models.rag_pipeline import initialize_rag_pipeline

# Initialize RAG
rag = initialize_rag_pipeline(
    index_dir="./data/index",
    model_name="llama-3.2-3b",  # Optimized for 8GB RAM
    quantize=True
)

# Ask question
result = rag.ask_question(
    query="What is the scope of ISO 9001?",
    top_k=5
)

print(f"Answer: {result['answer']}\n")
print(f"Sources ({result['num_sources']}):")
for source in result['sources']:
    print(f"  - {source['section']} ({source['section_name']}) [page {source['page']}]")
```

### Step 4: Run API Server

```bash
# Start server
python -m ml_core.api.api

# Or with uvicorn
uvicorn ml_core.api.api:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📘 Usage Guide

### Command-Line Tools

#### Ingest PDF
```bash
python -m ml_core.ingest.ingest_pipeline ./data/pdfs/ISO_9001.pdf ./data/chunks
```

#### Test PDF Extraction
```bash
python -m ml_core.ingest.pdf_to_text ./data/pdfs/sample.pdf
```

#### Test Embeddings
```bash
python -m ml_core.embeddings.embedder
```

### Python API

#### Custom Chunking Configuration

```python
from ml_core.ingest.chunker import DocumentChunker

chunker = DocumentChunker(
    target_tokens=400,
    min_tokens=200,
    max_tokens=600,
    overlap_tokens=50
)

chunks = chunker.chunk_sections(sections, "My Document")
```

#### Custom FAISS Index

```python
from ml_core.embeddings.build_faiss import FAISSIndexBuilder

builder = FAISSIndexBuilder(
    index_type="hnsw",  # Approximate search for faster queries
    metric="cosine"
)

index, metadata = builder.build_index(embeddings, metadata_list)
builder.save_index(index, metadata, "./custom_index")
```

---

## 🌐 API Documentation

### POST `/ask`

Ask a question and get an answer with sources.

**Request:**
```json
{
  "query": "What are the requirements for quality management?",
  "top_k": 5,
  "max_tokens": 512,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "answer": "According to ISO 9001 section 4.1...",
  "sources": [
    {
      "document": "ISO 9001",
      "section": "4.1",
      "section_name": "Understanding the Organization",
      "page": 5,
      "chunk_id": "iso_9001_4_1_chunk_0",
      "relevance_score": 0.872
    }
  ],
  "query": "What are the requirements...",
  "num_sources": 5,
  "timestamp": "2024-01-15T10:30:00"
}
```

### POST `/ingest`

Ingest a new PDF document.

**Request:**
```json
{
  "pdf_path": "/data/pdfs/ISO_14001.pdf",
  "document_name": "ISO 14001",
  "rebuild_index": true
}
```

**Response:**
```json
{
  "status": "success",
  "document_name": "ISO 14001",
  "chunks_created": 142,
  "sections_parsed": 28,
  "index_updated": true,
  "message": "Successfully ingested ISO 14001"
}
```

### GET `/info`

Get system status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model": "llama-3.2-3b",
  "index_size": 142,
  "index_directory": "./data/index",
  "uptime_seconds": 3600.5
}
```

---

## ⚙️ Configuration

Edit `ml_core/config/settings.yaml`:

```yaml
# LLM Configuration
llm:
  model_name: "llama-3.2-3b"  # Options: llama-3.2-3b, llama-3.1-8b, microsoft/Phi-3-mini-4k-instruct
  quantize: true  # REQUIRED for 8GB RAM
  max_tokens: 512
  temperature: 0.7

# Embeddings Configuration
embeddings:
  model_name: "BAAI/bge-small-en-v1.5"
  batch_size: 32
  device: "cpu"

# Chunking Configuration
chunking:
  target_tokens: 400
  overlap_tokens: 50

# FAISS Configuration
faiss:
  index_type: "flat"  # or "hnsw" for approximate search
  metric: "cosine"
```

---

## 🎓 Technical Choices

### Why BAAI/bge-small-en-v1.5?
- **Lightweight**: 384-dimensional embeddings
- **Fast**: Optimized for CPU inference
- **Accurate**: State-of-the-art performance on retrieval tasks
- **Multilingual**: Handles English and French ISO documents

### Why LLaMA 3.2 3B (4-bit quantized)?
- **Memory Efficient**: Fits in 8GB RAM with 4-bit quantization
- **Quality**: Better than many 7B+ models on instruction-following
- **CPU-Friendly**: Runs on Intel GPU systems without CUDA
- **Alternative**: Use LLaMA 3.1 8B if you have more RAM (16GB+)

### Why FAISS?
- **Fast**: Billion-scale vector search
- **Flexible**: Supports both exact (IndexFlatL2) and approximate (HNSW) search
- **Production-Ready**: Used by Meta, used at scale

### Chunking Strategy
- **Section-First**: Preserves ISO document structure
- **Smart Splitting**: Large sections split with 50-token overlap
- **Metadata Rich**: Every chunk knows its source section, page, document

---

## 📁 Project Structure

```
ml_core/
├── ingest/                     # Data ingestion pipeline
│   ├── pdf_to_text.py         # PDF extraction (Tesseract + PaddleOCR)
│   ├── clean_text.py          # Text cleaning
│   ├── parse_sections.py      # ISO section parsing
│   ├── chunker.py             # Intelligent chunking
│   └── ingest_pipeline.py     # End-to-end pipeline
│
├── embeddings/                 # Embeddings & search
│   ├── embedder.py            # BAAI/bge embeddings
│   ├── build_faiss.py         # FAISS index creation
│   └── search.py              # Semantic search
│
├── models/                     # RAG models
│   ├── llama_loader.py        # LLaMA with 4-bit quantization
│   ├── rag_pipeline.py        # Complete RAG pipeline
│   └── prompt_template.txt    # Prompt template
│
├── api/                        # REST API
│   └── api.py                 # FastAPI application
│
├── config/                     # Configuration
│   └── settings.yaml          # System configuration
│
├── tests/                      # Tests
│   └── test_rag.py            # Unit and integration tests
│
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
└── README.md                   # This file
```

---

## 🛠️ Troubleshooting

### Out of Memory (OOM) Errors

**Solution**: Ensure quantization is enabled

```python
# Use 4-bit quantization
rag = initialize_rag_pipeline(
    index_dir="./data/index",
    model_name="llama-3.2-3b",
    quantize=True  # REQUIRED for 8GB RAM
)
```

### PaddleOCR Not Working

**Solution**: Install with CPU support

```bash
pip install paddlepaddle paddleocr
```

Or disable PaddleOCR:
```python
result = extract_text_from_pdf(pdf_path, use_paddleocr=False)
```

### Tesseract Not Found

**Solution**: Install Tesseract OCR

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-fra

# Windows: Download installer from
# https://github.com/UB-Mannheim/tesseract/wiki

# macOS
brew install tesseract tesseract-lang
```

### Section Parsing Misses Sections

**Solution**: Adjust regex pattern

The parser looks for patterns like `4.1.2 Title`. If your ISO docs use different formatting, modify `parse_sections.py`:

```python
SECTION_PATTERN = r'^(\d+(?:\.\d+)*)\s+([A-ZÀ-ÿ][^\n]+?)$'
```

### FAISS Import Error on Windows

**Solution**: Use `faiss-cpu`:

```bash
pip uninstall faiss-gpu faiss
pip install faiss-cpu
```

---

## 📊 Performance

### Benchmarks (8GB RAM, Intel i5)

- **PDF Ingestion**: ~30 seconds for 50-page ISO document
- **Embedding Generation**: ~2 seconds for 100 chunks (batch_size=32)
- **FAISS Search**: <10ms for top-5 retrieval
- **RAG Answer**: ~5-15 seconds (4-bit LLaMA 3.2 3B)

### Optimization Tips

1. **Use HNSW for large datasets** (>10,000 chunks):
   ```yaml
   faiss:
     index_type: "hnsw"
   ```

2. **Increase batch size** on powerful CPUs:
   ```yaml
   embeddings:
     batch_size: 64
   ```

3. **Use smaller model** if speed is critical:
   ```yaml
   llm:
     model_name: "microsoft/Phi-3-mini-4k-instruct"
   ```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest ml_core/tests/ -v

# Run specific test
pytest ml_core/tests/test_rag.py::TestTextCleaning -v

# Run with coverage
pytest ml_core/tests/ --cov=ml_core --cov-report=html
```

---

## 📝 License

This project is part of a university assignment. For educational purposes.

---

## 🤝 Contributing

This is a student project, but suggestions are welcome!

1. Understand the codebase
2. Test your changes
3. Follow existing code style
4. Document technical decisions

---

## 📞 Support

For questions about the implementation, refer to:

- **Architecture**: See `implementation_plan.md`
- **Code Documentation**: Inline comments in each module
- **Examples**: Check `__main__` blocks in each Python file

---

**Built with ❤️ for ISO Document Navigation**

*Data Engineering + Machine Learning + MLOps*
