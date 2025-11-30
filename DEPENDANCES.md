# 📦 GUIDE DES DÉPENDANCES - ISO Document Navigator

## ✅ Ce qui se télécharge AUTOMATIQUEMENT

### 🤖 Modèle LLaMA 3.2 3B
- **Téléchargement :** AUTOMATIQUE lors du premier lancement
- **Source :** HuggingFace Hub
- **Taille :** ~3 GB (version quantifiée 4-bit)
- **Emplacement :** `C:\Users\hp\.cache\huggingface\hub\`
- **Temps :** 10-15 minutes (selon votre connexion)

### 🔢 Modèle d'embeddings BAAI/bge-small-en-v1.5
- **Téléchargement :** AUTOMATIQUE
- **Taille :** ~130 MB
- **Temps :** 1-2 minutes

**Vous n'avez RIEN à faire ! Le système gère tout automatiquement.**

---

## 📋 DÉPENDANCES À INSTALLER MANUELLEMENT

### 1️⃣ Dépendances Python (Backend ML)

**Fichier :** `ml_core/requirements.txt`

```bash
cd d:\iso-doc-navigator-main\ml_core
pip install -r requirements.txt
```

**Liste complète des packages :**

#### Bibliothèques ML Core
- `transformers>=4.35.0` - Pour LLaMA et modèles HuggingFace
- `sentence-transformers>=2.2.2` - Pour les embeddings BAAI
- `torch>=2.0.0` - PyTorch (CPU version)
- `accelerate>=0.24.0` - Accélération des modèles
- `bitsandbytes>=0.41.0` - Quantification 4-bit

#### Recherche vectorielle
- `faiss-cpu>=1.7.4` - Index vectoriel FAISS

#### Traitement PDF
- `pdfminer.six>=20221105` - Extraction texte PDF
- `PyMuPDF>=1.23.0` - Manipulation PDF (fitz)
- `pytesseract>=0.3.10` - OCR Tesseract
- `Pillow>=10.0.0` - Traitement d'images

#### OCR avancé (optionnel mais recommandé)
- `paddleocr>=2.7.0` - OCR avancé
- `paddlepaddle>=2.5.0` - Backend PaddleOCR

#### Traitement Word/Excel
- `python-docx>=1.1.0` - Lecture fichiers Word
- `openpyxl>=3.1.0` - Lecture fichiers Excel .xlsx
- `xlrd>=2.0.1` - Lecture fichiers Excel .xls

#### Utilitaires
- `numpy>=1.24.0` - Calculs numériques
- `tiktoken>=0.5.0` - Comptage de tokens

#### API Server
- `fastapi>=0.104.0` - Framework API
- `uvicorn[standard]>=0.24.0` - Serveur ASGI
- `pydantic>=2.0.0` - Validation données
- `python-multipart>=0.0.6` - Upload fichiers

#### Configuration
- `pyyaml>=6.0` - Fichiers YAML

#### Tests
- `pytest>=7.4.0` - Framework de tests
- `pytest-asyncio>=0.21.0` - Tests async

---

### 2️⃣ Dépendances Node.js (Frontend React)

**Fichier :** `iso-doc-navigator-main/package.json`

```bash
cd d:\iso-doc-navigator-main\iso-doc-navigator-main
npm install
```

**Packages principaux (déjà dans package.json) :**
- React 18.3.1
- Vite (build tool)
- TailwindCSS
- shadcn/ui components
- @tanstack/react-query (pour les appels API)
- sonner (notifications)

---

## 🚀 PROCESSUS D'INSTALLATION COMPLET

### Option A : Installation automatique (RECOMMANDÉ)

**Double-cliquez sur :** `install.bat`

Cela installe TOUT automatiquement :
1. ✅ Dépendances Python
2. ✅ Dépendances Node.js
3. ✅ Traite vos documents
4. ✅ Crée l'index FAISS

---

### Option B : Installation manuelle

#### Étape 1 : Dépendances Python
```powershell
cd d:\iso-doc-navigator-main\ml_core

# Installer les packages ML core
pip install -r requirements.txt

# Installer les packages Word/Excel
pip install python-docx openpyxl xlrd
```

⏱️ **Temps :** 5-7 minutes

#### Étape 2 : Dépendances Node.js
```powershell
cd d:\iso-doc-navigator-main\iso-doc-navigator-main

# Installer tous les packages npm
npm install

# Créer la configuration
echo VITE_ML_API_URL=http://localhost:8000 > .env.local
```

⏱️ **Temps :** 2-3 minutes

---

## 📥 TÉLÉCHARGEMENT DES MODÈLES ML

### Quand les modèles se téléchargent ?

**Au premier lancement du backend :**

```powershell
uvicorn ml_core.api.api:app --reload
```

**Vous verrez :**
```
Downloading (…)lve/main/config.json: 100%|███████| 899/899
Downloading model.safetensors: 100%|███████| 2.87G/2.87G
Loading checkpoint shards: 100%|███████| 2/2
```

### Où sont stockés les modèles ?

**Windows :**
```
C:\Users\hp\.cache\huggingface\hub\
├── models--meta-llama--Llama-3.2-3B-Instruct\
│   └── snapshots\
│       └── [hash]\
│           ├── model.safetensors
│           ├── config.json
│           └── ...
│
└── models--BAAI--bge-small-en-v1.5\
    └── snapshots\
        └── [hash]\
            └── ...
```

**Espace disque nécessaire :** ~3.5 GB total

---

## ⚙️ DÉPENDANCES SYSTÈME (Windows)

### Tesseract OCR (optionnel mais recommandé)

**Pour Windows :**
1. Télécharger : https://github.com/UB-Mannheim/tesseract/wiki
2. Installer l'exécutable
3. Ajouter au PATH : `C:\Program Files\Tesseract-OCR`

**Test :**
```powershell
tesseract --version
```

Si vous ne voulez pas installer Tesseract, PaddleOCR seul suffit.

---

## 🔍 VÉRIFIER LES INSTALLATIONS

### Python packages
```powershell
pip list | findstr transformers
pip list | findstr faiss
pip list | findstr fastapi
```

### Node packages
```powershell
npm list --depth=0
```

### Modèles téléchargés
```powershell
dir C:\Users\hp\.cache\huggingface\hub\
```

---

## 📊 RÉSUMÉ DES TÉLÉCHARGEMENTS

| Item | Taille | Temps (50 Mbps) | Auto/Manuel |
|------|--------|-----------------|-------------|
| Python packages | ~500 MB | 3 min | Manuel |
| Node packages | ~300 MB | 2 min | Manuel |
| LLaMA 3.2 3B | ~3 GB | 10 min | **AUTO** |
| BAAI embeddings | ~130 MB | 1 min | **AUTO** |
| **TOTAL** | **~4 GB** | **~15 min** | - |

---

## ✅ CHECKLIST D'INSTALLATION

Avant de lancer le chatbot, vérifiez :

- [ ] Python 3.10+ installé (`python --version`)
- [ ] Node.js installé (`node --version`)
- [ ] Dépendances Python installées (`pip install -r requirements.txt`)
- [ ] Dépendances Node installées (`npm install`)
- [ ] Documents placés dans `ml_core/data/pdfs/`
- [ ] Tesseract installé (optionnel)

**Ensuite :**
- [ ] Exécutez `install.bat` pour tout préparer
- [ ] Lancez `start.bat` pour démarrer le chatbot

---

## 🎯 EN RÉSUMÉ

### Vous devez installer :
1. ✅ Packages Python (via `pip install -r requirements.txt`)
2. ✅ Packages Node.js (via `npm install`)

### Le système télécharge AUTOMATIQUEMENT :
1. ✅ LLaMA 3.2 3B (~3 GB)
2. ✅ BAAI embeddings (~130 MB)

**Pas besoin de télécharger manuellement les modèles ! 🎉**
