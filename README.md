# 📚 ISO AI Navigator - AAAHF

**Système RAG intelligent pour la navigation et la conformité ISO**

Assistant IA basé sur LLaMA 3.2 3B pour répondre aux questions sur les normes ISO avec citations précises des sources.

---

## 🎯 Fonctionnalités

- ✅ **Extraction multi-format** : PDF, Word (.docx), Excel (.xlsx)
- ✅ **RAG Pipeline complet** : Embeddings BAAI + FAISS + LLaMA 3.2 3B
- ✅ **API REST** : FastAPI avec documentation Swagger
- ✅ **Interface React** : UI moderne et responsive
- ✅ **Citations de sources** : Chaque réponse inclut les sections ISO référencées
- ✅ **Optimisé CPU** : Fonctionne sans GPU (8GB RAM minimum)

---

## 🚀 Installation rapide

### Prérequis
- Python 3.10+
- Node.js 16+
- 8GB RAM minimum
- Connexion internet (pour télécharger les modèles)

### Installation

```bash
# Cloner le repo
git clone https://github.com/AsamaeS/ISO_ai_AAAHF.git
cd ISO_ai_AAAHF

# Option 1 : Installation automatique (Windows)
.\install.bat

# Option 2 : Installation manuelle
cd ml_core
pip install -r requirements.txt
pip install python-docx openpyxl xlrd

cd ../iso-doc-navigator-main
npm install
echo VITE_ML_API_URL=http://localhost:8000 > .env.local
```

---

## 📄 Préparer vos documents

1. Placez vos PDFs ISO dans `ml_core/data/pdfs/`
2. Traitez les documents :

```bash
cd ml_core
python -m ml_core.ingest.batch_processor ./data/pdfs ./data/chunks ./data/index
```

⏱️ Temps : 3-5 minutes pour ~10 documents

---

## 🎮 Lancement

### Backend (API ML)

```bash
cd ml_core
python -m uvicorn ml_core.api.api:app --reload --host 0.0.0.0 --port 8000
```

🕒 **Premier lancement** : 10-15 min (télécharge LLaMA 3.2 3B ~3GB)  
🕒 **Lancements suivants** : 30 secondes

### Frontend (Interface React)

```bash
cd iso-doc-navigator-main
npm run dev
```

---

## 🌐 Accès

- **Interface utilisateur** : http://localhost:5173
- **API Documentation** : http://localhost:8000/docs
- **Backend API** : http://localhost:8000

---

## 📚 Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Documents  │────▶│  Ingestion   │────▶│  Embeddings │
│  ISO (PDF)  │     │   Pipeline   │     │  (BAAI/bge) │
└─────────────┘     └──────────────┘     └─────────────┘
                                                  │
                                                  ▼
                    ┌──────────────┐     ┌─────────────┐
                    │    LLaMA     │◀────│    FAISS    │
                    │  3.2 3B 4bit │     │    Index    │
                    └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   FastAPI    │
                    │  REST API    │
                    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  React UI    │
                    └──────────────┘
```

---

## 🛠️ Technologies

### Backend ML
- **LLM** : LLaMA 3.2 3B Instruct (4-bit quantized)
- **Embeddings** : BAAI/bge-small-en-v1.5 (384 dim)
- **Vector DB** : FAISS (Facebook AI Similarity Search)
- **API** : FastAPI + Uvicorn
- **OCR** : Tesseract + PaddleOCR

### Frontend
- **Framework** : React 18 + Vite
- **UI** : TailwindCSS + shadcn/ui
- **State** : React Query (@tanstack/react-query)
- **Router** : React Router v6

---

## 📖 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Guide de démarrage en 3 étapes
- **[LANCEMENT.md](LANCEMENT.md)** - Instructions détaillées de lancement
- **[DEPENDANCES.md](DEPENDANCES.md)** - Informations sur les modèles ML
- **[TEST_GUIDE.md](ml_core/TEST_GUIDE.md)** - Guide de test complet
- **[INTEGRATION.md](INTEGRATION.md)** - Intégration Frontend ↔️ Backend

---

## 🎓 Projet universitaire

Ce projet a été développé dans le cadre d'un cours de Machine learning.

**Objectifs pédagogiques accomplis :**
- ✅ Pipeline ETL complet (PDF → Chunks → Embeddings)
- ✅ Intégration de modèles ML (LLaMA, BAAI)
- ✅ Optimisation pour contraintes matérielles (8GB RAM, CPU-only)
- ✅ Déploiement d'API REST
- ✅ Containerisation Docker
- ✅ Tests unitaires et d'intégration

---

## ⚙️ Configuration

Éditez `ml_core/config/settings.yaml` pour personnaliser :

```yaml
# Modèle LLM
llm:
  model_name: "llama-3.2-3b"  # ou llama-3.1-8b
  quantize: true              # REQUIS pour 8GB RAM
  temperature: 0.7

# Embeddings
embeddings:
  model_name: "BAAI/bge-small-en-v1.5"
  device: "cpu"

# Chunking
chunking:
  target_tokens: 400
  overlap_tokens: 50
```

---

## 🐳 Déploiement Docker

```bash
# Construire et lancer
docker-compose up -d

# Accéder
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
```

---

## 🧪 Tests

```bash
cd ml_core
pytest tests/ -v
```

---

## 📊 Performance

**Configuration testée :** Intel i5, 8GB RAM, CPU uniquement

| Opération | Temps |
|-----------|-------|
| Ingestion PDF (50 pages) | ~30 secondes |
| Génération embeddings (100 chunks) | ~2 secondes |
| Recherche FAISS | <10 ms |
| Réponse RAG complète | 10-20 secondes |

---

## ⚠️ Notes importantes

### Modèles ML
Les modèles ne sont **PAS inclus** dans le repo (trop gros). Ils sont téléchargés automatiquement au premier lancement :
- LLaMA 3.2 3B : ~3 GB
- BAAI embeddings : ~130 MB

**Stockage :** `C:\Users\[USER]\.cache\huggingface\`

### Données
Les documents ISO et les index FAISS ne sont **PAS inclus** dans le repo. Vous devez :
1. Ajouter vos propres PDFs ISO dans `ml_core/data/pdfs/`
2. Exécuter le batch processor pour créer l'index

---

## 🤝 Contribution

Projet académique - suggestions bienvenues !

---

## 📝 Licence

Projet universitaire - Usage éducatif

---

## 👥 Auteurs
Asmae 
Amina
Anas
Hafsa
Fatem Zahra
**Équipe AAAHF**  
Projet ML

---

## 🔗 Liens utiles

- [LLaMA 3.2](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct)
- [BAAI/bge](https://huggingface.co/BAAI/bge-small-en-v1.5)
- [FAISS](https://github.com/facebookresearch/faiss)
- [FastAPI](https://fastapi.tiangolo.com/)

---

**Built with ❤️ for ISO Compliance**
