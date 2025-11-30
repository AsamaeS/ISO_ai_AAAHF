"""
FastAPI REST API for RAG Pipeline

Provides endpoints for:
- Question answering (/ask)
- Document ingestion (/ingest)
- Health check (/info)
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..ingest.ingest_pipeline import IngestionPipeline
from ..embeddings.embedder import Embedder
from ..embeddings.build_faiss import build_index_from_chunks
from ..models.rag_pipeline import RAGPipeline, initialize_rag_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Request/Response Models
class AskRequest(BaseModel):
    """Request model for /ask endpoint."""
    query: str = Field(..., description="User question", min_length=1)
    top_k: int = Field(default=5, description="Number of chunks to retrieve", ge=1, le=20)
    max_tokens: int = Field(default=512, description="Max tokens for answer", ge=50, le=2048)
    temperature: float = Field(default=0.7, description="LLM temperature", ge=0.0, le=2.0)


class Source(BaseModel):
    """Source citation model."""
    document: str
    section: str
    section_name: str
    page: int
    chunk_id: str
    relevance_score: float


class AskResponse(BaseModel):
    """Response model for /ask endpoint."""
    answer: str
    sources: List[Source]
    query: str
    num_sources: int
    timestamp: str


class IngestRequest(BaseModel):
    """Request model for /ingest endpoint."""
    pdf_path: str = Field(..., description="Path to PDF file")
    document_name: Optional[str] = Field(None, description="Document name (defaults to filename)")
    rebuild_index: bool = Field(default=True, description="Rebuild FAISS index after ingestion")


class IngestResponse(BaseModel):
    """Response model for /ingest endpoint."""
    status: str
    document_name: str
    chunks_created: int
    sections_parsed: int
    index_updated: bool
    message: str


class InfoResponse(BaseModel):
    """Response model for /info endpoint."""
    status: str
    version: str
    model: str
    index_size: int
    index_directory: str
    uptime_seconds: float


# Global state
app_state = {
    'rag_pipeline': None,
    'start_time': datetime.now(),
    'config': {}
}


# FastAPI app
app = FastAPI(
    title="ISO Document RAG API",
    description="Semantic search and question answering for ISO documents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize RAG pipeline on startup."""
    logger.info("Starting API server...")
    
    # Load configuration
    index_dir = app_state['config'].get('index_dir', './ml_core/data/index')
    model_name = app_state['config'].get('model_name', 'llama-3.2-3b')
    quantize = app_state['config'].get('quantize', True)
    
    # Check if index exists
    index_path = Path(index_dir)
    if index_path.exists() and (index_path / "faiss_index.bin").exists():
        logger.info(f"Loading RAG pipeline from: {index_dir}")
        try:
            app_state['rag_pipeline'] = initialize_rag_pipeline(
                index_dir=index_dir,
                model_name=model_name,
                quantize=quantize
            )
            logger.info("✓ RAG pipeline loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load RAG pipeline: {e}")
            logger.warning("API will start without RAG pipeline. Use /ingest to create index.")
    else:
        logger.warning(f"No index found at {index_dir}")
        logger.warning("API starting without RAG pipeline. Use /ingest to create index.")


@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Ask a question and get an answer with sources.
    
    **Example request:**
    ```json
    {
        "query": "What is the scope of ISO 9001?",
        "top_k": 5,
        "temperature": 0.7
    }
    ```
    """
    if app_state['rag_pipeline'] is None:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized. Please run /ingest first to create index."
        )
    
    try:
        logger.info(f"Processing question: {request.query}")
        
        # Get answer from RAG pipeline
        result = app_state['rag_pipeline'].ask_question(
            query=request.query,
            top_k=request.top_k,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Format response
        response = AskResponse(
            answer=result['answer'],
            sources=[Source(**s) for s in result['sources']],
            query=result['query'],
            num_sources=result['num_sources'],
            timestamp=datetime.now().isoformat()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Ingest a PDF document into the system.
    
    **Example request:**
    ```json
    {
        "pdf_path": "/data/pdfs/ISO_9001.pdf",
        "document_name": "ISO 9001",
        "rebuild_index": true
    }
    ```
    """
    pdf_path = Path(request.pdf_path)
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF file not found: {request.pdf_path}")
    
    try:
        logger.info(f"Starting ingestion: {pdf_path}")
        
        # Run ingestion pipeline
        output_dir = app_state['config'].get('output_dir', './data/chunks')
        
        pipeline = IngestionPipeline()
        result = pipeline.ingest_document(
            str(pdf_path),
            document_name=request.document_name,
            output_dir=output_dir
        )
        
        chunks = result['chunks']
        document_name = result['document_name']
        
        logger.info(f"Ingestion complete: {len(chunks)} chunks created")
        
        # Rebuild index if requested
        index_updated = False
        if request.rebuild_index:
            logger.info("Rebuilding FAISS index...")
            
            index_dir = app_state['config'].get('index_dir', './data/index')
            
            # Generate embeddings
            embedder = Embedder()
            texts = [c['text'] for c in chunks]
            embeddings = embedder.embed_texts(texts, show_progress=True)
            
            # Build index
            build_index_from_chunks(chunks, embeddings, index_dir)
            
            index_updated = True
            logger.info("Index rebuilt successfully")
            
            # Reload RAG pipeline in background
            background_tasks.add_task(reload_rag_pipeline, index_dir)
        
        return IngestResponse(
            status="success",
            document_name=document_name,
            chunks_created=len(chunks),
            sections_parsed=len(result['sections']),
            index_updated=index_updated,
            message=f"Successfully ingested {document_name}"
        )
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info", response_model=InfoResponse)
async def get_info():
    """
    Get API information and status.
    """
    uptime = (datetime.now() - app_state['start_time']).total_seconds()
    
    # Get index size
    index_size = 0
    index_dir = app_state['config'].get('index_dir', './data/index')
    
    if app_state['rag_pipeline'] is not None:
        index_size = app_state['rag_pipeline'].search_engine.index.ntotal
    
    return InfoResponse(
        status="healthy" if app_state['rag_pipeline'] is not None else "no_index",
        version="1.0.0",
        model=app_state['config'].get('model_name', 'llama-3.2-3b'),
        index_size=index_size,
        index_directory=index_dir,
        uptime_seconds=uptime
    )


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


async def reload_rag_pipeline(index_dir: str):
    """Reload RAG pipeline (background task)."""
    try:
        logger.info("Reloading RAG pipeline...")
        model_name = app_state['config'].get('model_name', 'llama-3.2-3b')
        quantize = app_state['config'].get('quantize', True)
        
        app_state['rag_pipeline'] = initialize_rag_pipeline(
            index_dir=index_dir,
            model_name=model_name,
            quantize=quantize
        )
        logger.info("✓ RAG pipeline reloaded")
    except Exception as e:
        logger.error(f"Failed to reload RAG pipeline: {e}")


def create_app(config: dict = None) -> FastAPI:
    """
    Create and configure FastAPI app.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured FastAPI app
    """
    if config:
        app_state['config'] = config
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    config = {
        'index_dir': './ml_core/data/index',
        'output_dir': './ml_core/data/chunks',
        'model_name': 'llama-3.2-3b',
        'quantize': True
    }
    
    app_state['config'] = config
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
