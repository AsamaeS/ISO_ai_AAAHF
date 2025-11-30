# 🧪 Guide de Test - Pipeline RAG Complet

## 📋 Installation des dépendances

```bash
cd d:\iso-doc-navigator-main\ml_core

# Installer toutes les dépendances ML
pip install -r requirements.txt

# Installer les dépendances Word/Excel
pip install python-docx openpyxl xlrd
```

## 🚀 Test Étape par Étape

### Étape 1 : Traiter UN document (test rapide)

```bash
# Tester avec un seul PDF ISO
python -m ml_core.ingest.document_extractor "./data/pdfs/Normes_Standard-20251129T161324Z-1-001/Normes_Standard/ISO_9001_V_2015_Fr.pdf"
```

### Étape 2 : Traiter TOUS les documents

```bash
# Traitement en batch (tous formats)
python -m ml_core.ingest.batch_processor "./data/pdfs" "./data/chunks" "./data/index"
```

**Attendu :**
- ✅ 2 PDFs ISO traités
- ✅ 8 fichiers Excel traités  
- ✅ 2 fichiers Word traités
- ✅ Total : ~12 documents
- ✅ Index FAISS créé

### Étape 3 : Vérifier les résultats

```bash
# Vérifier les chunks générés
dir data\chunks

# Vérifier l'index FAISS
dir data\index
```

**Fichiers attendus :**
- `all_documents_chunks.json` - Tous les chunks
- `faiss_index.bin` - Index vectoriel
- `faiss_index_metadata.json` - Métadonnées

### Étape 4 : Tester le RAG (sans démarrer l'API)

```python
from ml_core.models.rag_pipeline import initialize_rag_pipeline

# Charger le système
rag = initialize_rag_pipeline(
    index_dir="./data/index",
    model_name="llama-3.2-3b",
    quantize=True
)

# Poser une question
result = rag.ask_question(
    query="Qu'est-ce que l'ISO 9001 ?",
    top_k=5
)

print("Réponse:", result['answer'])
print("\nSources:")
for s in result['sources']:
    print(f"  - {s['document']} [{s['section']}] p.{s['page']}")
```

### Étape 5 : Lancer l'API

```bash
# Démarrer le serveur FastAPI
uvicorn ml_core.api.api:app --reload --host 0.0.0.0 --port 8000

# Tester avec curl
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Qu'est-ce que l'ISO 9001?\", \"top_k\": 3}"
```

### Étape 6 : Lancer le frontend

```bash
cd ../iso-doc-navigator-main

# Créer .env.local
echo VITE_ML_API_URL=http://localhost:8000 > .env.local

# Démarrer React
npm run dev
```

Ouvrir : http://localhost:5173

## ⏱️ Temps estimés

| Étape | Temps (première fois) | Temps (suivantes) |
|-------|----------------------|-------------------|
| Installation deps | 5 min | - |
| Traitement docs | 3-5 min | 2 min |
| Téléchargement LLaMA | 10-15 min | - |
| Chargement LLaMA | 2-3 min | 30 sec |
| Question RAG | 10-20 sec | 10-20 sec |

## 🐛 Dépannage

### Erreur: "No module named 'ml_core'"
```bash
# Assurez-vous d'être dans le bon dossier
cd d:\iso-doc-navigator-main
python -m ml_core.ingest.batch_processor ...
```

### Erreur: "CUDA not available"
✅ C'est normal ! Le système utilise CPU + quantification 4-bit

### Erreur: "Out of memory"
- Fermez les autres applications
- Le modèle quantifié devrait tenir dans 8GB RAM
- Si problème persiste, utilisez un modèle plus petit

### Erreur: "python-docx not found"
```bash
pip install python-docx openpyxl xlrd
```

## 📊 Résultats attendus

```
Traitement des documents :
- ISO_9001_V_2015_Fr.pdf ✅ → ~150 chunks
- ISO 9000v2015.pdf ✅ → ~120 chunks
- 8 fichiers Excel ✅ → ~50 chunks
- 2 fichiers Word ✅ → ~30 chunks

Total: ~350 chunks
Index FAISS: ~3 MB
```

## ✅ Validation

1. **Chunks créés** : `data/chunks/all_documents_chunks.json` existe
2. **Index FAISS** : `data/index/faiss_index.bin` existe
3. **API fonctionne** : http://localhost:8000/docs accessible
4. **Frontend connecté** : Questions/réponses fonctionnent

## 🎯 Questions de test suggérées

1. "Qu'est-ce que l'ISO 9001 ?"
2. "Comment gérer la formation du personnel ?"
3. "Quelles sont les procédures de non-conformité ?"
4. "Quelle est la matrice de compétences ?"
5. "Comment évaluer une formation ?"

Ces questions couvrent vos 3 types de documents (ISO PDF, Excel formation, Word procédures).
