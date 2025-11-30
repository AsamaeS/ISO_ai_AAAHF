"""
Quick Start Example - Complete RAG Pipeline Demo

This script demonstrates the complete workflow:
1. Ingest a PDF
2. Build FAISS index
3. Ask questions with RAG
"""

import json
from pathlib import Path

# Import pipeline components
from ml_core.ingest.ingest_pipeline import ingest_document
from ml_core.embeddings.embedder import Embedder
from ml_core.embeddings.build_faiss import build_index_from_chunks
from ml_core.models.rag_pipeline import initialize_rag_pipeline


def main():
    """Run complete RAG pipeline demo."""
    
    print("=" * 70)
    print("🚀 ML CORE RAG PIPELINE - QUICK START DEMO")
    print("=" * 70)
    
    # Configuration
    pdf_path = "./data/pdfs/sample_iso.pdf"  # Replace with your PDF
    output_dir = "./data/chunks"
    index_dir = "./data/index"
    
    # ========================================================================
    # STEP 1: INGEST PDF DOCUMENT
    # ========================================================================
    print("\n📄 STEP 1: Ingesting PDF document...")
    print(f"   Input: {pdf_path}")
    
    if Path(pdf_path).exists():
        result = ingest_document(
            pdf_path=pdf_path,
            document_name="ISO Sample",
            output_dir=output_dir
        )
        
        chunks = result['chunks']
        print(f"   ✅ Created {len(chunks)} chunks")
        print(f"   ✅ Parsed {len(result['sections'])} sections")
        print(f"   ✅ Saved to: {output_dir}/ISO_Sample_chunks.json")
    else:
        print(f"   ⚠️  PDF not found at {pdf_path}")
        print(f"   Loading existing chunks from {output_dir}...")
        chunks_file = Path(output_dir) / "ISO_Sample_chunks.json"
        
        if chunks_file.exists():
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            print(f"   ✅ Loaded {len(chunks)} chunks")
        else:
            print("   ❌ No chunks found. Please provide a PDF file.")
            return
    
    # ========================================================================
    # STEP 2: GENERATE EMBEDDINGS AND BUILD FAISS INDEX
    # ========================================================================
    print("\n🔢 STEP 2: Generating embeddings...")
    
    embedder = Embedder(device="cpu")
    texts = [chunk['text'] for chunk in chunks]
    
    print(f"   Embedding {len(texts)} chunks with BAAI/bge-small-en-v1.5...")
    embeddings = embedder.embed_texts(texts, show_progress=True)
    
    print(f"   ✅ Embeddings shape: {embeddings.shape}")
    print(f"   ✅ Dimension: {embedder.embedding_dim}")
    
    print("\n📊 STEP 3: Building FAISS index...")
    build_index_from_chunks(
        chunks,
        embeddings,
        output_dir=index_dir,
        index_type="flat"
    )
    
    print(f"   ✅ FAISS index saved to: {index_dir}")
    
    # ========================================================================
    # STEP 4: INITIALIZE RAG PIPELINE
    # ========================================================================
    print("\n🤖 STEP 4: Loading RAG pipeline...")
    print("   Note: Loading LLaMA 3.2 3B with 4-bit quantization...")
    print("   This may take 2-3 minutes on first run (downloads model)...")
    
    rag = initialize_rag_pipeline(
        index_dir=index_dir,
        model_name='llama-3.2-3b',  # Optimized for 8GB RAM
        quantize=True  # Essential for memory efficiency
    )
    
    print("   ✅ RAG pipeline ready!")
    
    # ========================================================================
    # STEP 5: ASK QUESTIONS
    # ========================================================================
    print("\n" + "=" * 70)
    print("💬 STEP 5: Asking questions...")
    print("=" * 70)
    
    # Example questions
    questions = [
        "What is the scope of this ISO standard?",
        "What are the main requirements?",
        "Qu'est-ce que le contexte de l'organisme?"  # French question
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'—' * 70}")
        print(f"❓ Question {i}: {question}")
        print('—' * 70)
        
        result = rag.ask_question(
            query=question,
            top_k=3,
            max_tokens=256,
            temperature=0.7
        )
        
        print(f"\n💡 Answer:")
        print(f"   {result['answer']}")
        
        print(f"\n📚 Sources ({result['num_sources']}):")
        for j, source in enumerate(result['sources'], 1):
            print(f"   {j}. {source['document']} - Section {source['section']}")
            print(f"      {source['section_name']} [Page {source['page']}, Score: {source['relevance_score']:.3f}]")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE!")
    print("=" * 70)
    print("\n📋 Next Steps:")
    print("   1. Run API server: uvicorn ml_core.api.api:app --reload")
    print("   2. Test API: http://localhost:8000/docs")
    print("   3. Ingest more PDFs: POST /ingest")
    print("   4. Ask questions: POST /ask")
    print("\n🐳 Docker Deployment:")
    print("   docker-compose up -d")
    print("   Visit: http://localhost:8000/docs")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Demo interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
