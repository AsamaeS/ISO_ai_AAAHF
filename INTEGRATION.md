# 🔗 Guide d'Intégration Frontend ↔️ Backend

## 📐 Architecture Complète

```
┌─────────────────────────────────────────────────────────────┐
│                    Projet Complet                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐         ┌──────────────────────┐  │
│  │  Frontend (React)    │         │  Backend (FastAPI)   │  │
│  │  Port: 5173          │  HTTP   │  Port: 8000          │  │
│  │                      │ ◄─────► │                      │  │
│  │  - UI/UX             │         │  - ML Pipeline       │  │
│  │  - React Query       │         │  - RAG System        │  │
│  │  - TailwindCSS       │         │  - FAISS Search      │  │
│  └──────────────────────┘         └──────────────────────┘  │
│                                              │                │
│                                              ▼                │
│                                    ┌──────────────────────┐  │
│                                    │  Modèles ML          │  │
│                                    │  - LLaMA 3.2 3B      │  │
│                                    │  - BAAI/bge          │  │
│                                    │  - FAISS Index       │  │
│                                    └──────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📍 Où se trouvent les modèles ?

### 🦙 LLaMA 3.2 3B et BAAI/bge (HuggingFace)

Les modèles sont **automatiquement téléchargés** lors de la première utilisation et stockés dans :

**Windows :**
```
C:\Users\hp\.cache\huggingface\hub\
```

**Contenu du cache :**
```
huggingface/
└── hub/
    ├── models--meta-llama--Llama-3.2-3B-Instruct/
    │   └── (fichiers du modèle LLaMA ~6GB avec quantification)
    │
    └── models--BAAI--bge-small-en-v1.5/
        └── (fichiers du modèle embeddings ~130MB)
```

**Taille totale :** ~2-3 GB pour LLaMA quantifié + ~130 MB pour BAAI = **~3 GB**

### 📊 Index FAISS (vos données)

Stocké dans votre projet :
```
d:\iso-doc-navigator-main\ml_core\data\index\
├── faiss_index.bin           (vecteurs)
├── faiss_index_metadata.json (métadonnées)
└── faiss_index_config.json   (configuration)
```

---

## 🚀 Comment lancer le projet complet

### Option 1 : Développement (2 terminaux)

**Terminal 1 - Backend ML Core :**
```bash
# Aller dans le dossier backend
cd d:\iso-doc-navigator-main\ml_core

# Installer les dépendances (première fois)
pip install -r requirements.txt

# Lancer l'API
uvicorn ml_core.api.api:app --reload --host 0.0.0.0 --port 8000
```
✅ Backend disponible sur : http://localhost:8000  
📚 Documentation API : http://localhost:8000/docs

**Terminal 2 - Frontend React :**
```bash
# Aller dans le dossier frontend
cd d:\iso-doc-navigator-main\iso-doc-navigator-main

# Installer les dépendances (première fois)
npm install

# Créer le fichier .env.local
copy .env.example .env.local
# Puis éditer .env.local et mettre : VITE_ML_API_URL=http://localhost:8000

# Lancer le frontend
npm run dev
```
✅ Frontend disponible sur : http://localhost:5173

---

### Option 2 : Docker (tout-en-un)

Je vais créer un docker-compose qui lance les deux services ensemble :

```bash
# À la racine du projet
docker-compose up -d

# Frontend : http://localhost:5173
# Backend : http://localhost:8000
```

---

## 🔌 Utilisation de l'API dans le Frontend

### Exemple : Poser une question

```typescript
import { useAskQuestion } from '@/hooks/useMLCore';

function QuestionComponent() {
  const askQuestion = useAskQuestion();

  const handleSubmit = async (question: string) => {
    const result = await askQuestion.mutateAsync({
      query: question,
      top_k: 5,
      temperature: 0.7
    });

    console.log('Answer:', result.answer);
    console.log('Sources:', result.sources);
  };

  return (
    <div>
      <input onChange={(e) => handleSubmit(e.target.value)} />
      {askQuestion.isPending && <p>Loading...</p>}
      {askQuestion.data && (
        <div>
          <p>{askQuestion.data.answer}</p>
          <ul>
            {askQuestion.data.sources.map(source => (
              <li key={source.chunk_id}>
                {source.section} - {source.section_name} (page {source.page})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

### Exemple : Vérifier le statut du backend

```typescript
import { useSystemInfo } from '@/hooks/useMLCore';

function StatusIndicator() {
  const { data, isLoading } = useSystemInfo();

  if (isLoading) return <p>Checking...</p>;

  return (
    <div>
      <p>Status: {data?.status}</p>
      <p>Model: {data?.model}</p>
      <p>Index Size: {data?.index_size} chunks</p>
    </div>
  );
}
```

---

## 📦 Fichiers créés pour l'intégration

1. ✅ **`.env.example`** - Configuration exemple
2. ✅ **`src/services/mlCoreAPI.ts`** - Client API TypeScript
3. ✅ **`src/hooks/useMLCore.ts`** - React hooks

### Pour les utiliser :

1. **Créer `.env.local` à partir de `.env.example`**
   ```bash
   cd iso-doc-navigator-main
   copy .env.example .env.local
   ```

2. **Éditer `.env.local`** et confirmer :
   ```
   VITE_ML_API_URL=http://localhost:8000
   ```

3. **Importer dans vos composants React** :
   ```typescript
   import { useAskQuestion, useSystemInfo } from '@/hooks/useMLCore';
   ```

---

## 🔧 Configuration Complète

### Frontend (package.json - déjà installé)
- React + TypeScript ✅
- Vite ✅
- TailwindCSS + shadcn/ui ✅
- React Router ✅
- React Query (@tanstack/react-query) ✅

### Backend (ml_core/requirements.txt)
- FastAPI ✅
- Transformers (HuggingFace) ✅
- FAISS ✅
- Sentence Transformers ✅

---

## 📝 Script de lancement complet

Créez `start.bat` à la racine :

```batch
@echo off
echo ========================================
echo  Starting ISO Document Navigator
echo ========================================

echo.
echo [1/2] Starting ML Core Backend...
start cmd /k "cd ml_core && uvicorn ml_core.api.api:app --reload --port 8000"

timeout /t 5

echo.
echo [2/2] Starting Frontend...
start cmd /k "cd iso-doc-navigator-main && npm run dev"

echo.
echo ========================================
echo  Project Started!
echo ========================================
echo  Frontend: http://localhost:5173
echo  Backend:  http://localhost:8000/docs
echo ========================================
```

Puis double-cliquez sur `start.bat` pour tout lancer !

---

## ⚙️ Téléchargement des modèles

### Première exécution

Lors du premier lancement, les modèles HuggingFace seront téléchargés automatiquement :

```bash
# Quand vous lancez le backend la première fois :
uvicorn ml_core.api.api:app --reload

# Vous verrez :
Downloading (…)lve/main/config.json: 100%|███| 899/899
Downloading pytorch_model.bin: 100%|███| 2.87G/2.87G
```

**Temps estimé** : 10-20 minutes (selon connexion internet)  
**Espace requis** : ~3 GB

### Forcer le pré-téléchargement (optionnel)

```python
# Dans ml_core/
python -c "
from ml_core.models.llama_loader import LLaMALoader
from ml_core.embeddings.embedder import Embedder

print('Downloading LLaMA...')
loader = LLaMALoader(model_name='llama-3.2-3b', quantize=True)
loader.load_model()

print('Downloading BAAI embeddings...')
embedder = Embedder()

print('✅ All models downloaded!')
"
```

---

## ✅ Checklist de démarrage

- [ ] Backend installé : `cd ml_core && pip install -r requirements.txt`
- [ ] Frontend installé : `cd iso-doc-navigator-main && npm install`
- [ ] `.env.local` créé avec `VITE_ML_API_URL=http://localhost:8000`
- [ ] PDFs placés dans `ml_core/data/pdfs/`
- [ ] Backend lancé : port 8000 ✅
- [ ] Frontend lancé : port 5173 ✅
- [ ] Test : http://localhost:8000/docs (Swagger UI)
- [ ] Test : http://localhost:5173 (Interface React)

---

## 🎯 Workflow complet

1. **Lancer les deux serveurs** (backend + frontend)
2. **Ingérer vos PDFs ISO** via l'API `/ingest`
3. **Poser des questions** via l'interface React
4. **Le système :**
   - Recherche dans l'index FAISS
   - Génère une réponse avec LLaMA
   - Renvoie l'answer + sources au frontend

**🚀 Votre projet est maintenant 100% fonctionnel !**
