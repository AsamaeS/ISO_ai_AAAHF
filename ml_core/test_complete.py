"""
Script de test rapide - Traitement de tous vos documents

Ce script va :
1. Installer les dépendances
2. Traiter tous les documents (PDF, Word, Excel)
3. Créer l'index FAISS
4. Tester avec des questions
"""

import subprocess
import sys
from pathlib import Path

print("=" * 70)
print("🚀 TEST COMPLET DU PIPELINE RAG")
print("=" * 70)

# Étape 1 : Installation des dépendances
print("\n📦 Étape 1/4 : Installation des dépendances...")
print("-" * 70)

try:
    subprocess.run([
        sys.executable, "-m", "pip", "install", 
        "python-docx", "openpyxl", "xlrd"
    ], check=True)
    print("✅ Dépendances Word/Excel installées")
except Exception as e:
    print(f"⚠️  Erreur installation : {e}")
    print("Continuons quand même...")

# Étape 2 : Traiter tous les documents
print("\n📄 Étape 2/4 : Traitement des documents...")
print("-" * 70)

from ml_core.ingest.batch_processor import process_directory

try:
    result = process_directory(
        input_dir="./data/pdfs",
        output_dir="./data/chunks",
        index_dir="./data/index"
    )
    
    print(f"\n✅ Traitement terminé !")
    print(f"   - Fichiers traités : {result['processed']}/{result['total_files']}")
    print(f"   - Total chunks : {result['total_chunks']}")
    print(f"   - Index FAISS : {result['index_dir']}")
    
except Exception as e:
    print(f"❌ Erreur lors du traitement : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Étape 3 : Vérifier l'index
print("\n🔍 Étape 3/4 : Vérification de l'index...")
print("-" * 70)

index_file = Path("./data/index/faiss_index.bin")
if index_file.exists():
    print(f"✅ Index FAISS créé : {index_file}")
    print(f"   Taille : {index_file.stat().st_size / 1024:.2f} KB")
else:
    print("❌ Index FAISS non trouvé")
    sys.exit(1)

# Étape 4 : Test avec des questions
print("\n💬 Étape 4/4 : Test du système RAG...")
print("-" * 70)

try:
    from ml_core.models.rag_pipeline import initialize_rag_pipeline
    
    print("⏳ Chargement du modèle LLaMA (peut prendre 2-3 minutes)...")
    
    rag = initialize_rag_pipeline(
        index_dir="./data/index",
        model_name="llama-3.2-3b",
        quantize=True
    )
    
    print("✅ Modèle chargé !\n")
    
    # Questions de test
    questions = [
        "Qu'est-ce que l'ISO 9001 ?",
        "Quels sont les besoins en formation ?",
        "Comment gérer les non-conformités ?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*70}")
        print(f"❓ Question {i} : {question}")
        print('='*70)
        
        try:
            result = rag.ask_question(
                query=question,
                top_k=3,
                max_tokens=200,
                temperature=0.7
            )
            
            print(f"\n💡 Réponse :")
            print(f"   {result['answer']}\n")
            
            print(f"📚 Sources ({result['num_sources']}) :")
            for j, source in enumerate(result['sources'], 1):
                print(f"   {j}. {source['document']} - {source['section']} ({source['section_name']})")
                print(f"      Page {source['page']}, Score: {source['relevance_score']:.3f}")
        
        except Exception as e:
            print(f"❌ Erreur : {e}")
            import traceback
            traceback.print_exc()

except Exception as e:
    print(f"❌ Erreur lors de l'initialisation RAG : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Conclusion
print("\n" + "=" * 70)
print("✅ TEST TERMINÉ !")
print("=" * 70)
print("\n📋 Prochaines étapes :")
print("   1. Lancer l'API : uvicorn ml_core.api.api:app --reload")
print("   2. Lancer le frontend : cd ../iso-doc-navigator-main && npm run dev")
print("   3. Ouvrir http://localhost:5173")
print("=" * 70)
