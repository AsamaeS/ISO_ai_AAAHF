# 🚀 GUIDE DE LANCEMENT - Chatbot ISO Navigator

## ✅ Avant de commencer

Vérifiez que vous avez :
- [ ] Python 3.10+ installé
- [ ] Node.js installé
- [ ] Les fichiers ISO dans `ml_core/data/pdfs/`

---

## 🎯 ÉTAPE 1 : Préparer les données (À FAIRE UNE SEULE FOIS)

### 1.1 Installer les dépendances Python

Ouvrez un terminal PowerShell et exécutez :

```powershell
cd d:\iso-doc-navigator-main\ml_core
pip install -r requirements.txt
pip install python-docx openpyxl xlrd
```

⏱️ **Temps estimé :** 5 minutes

### 1.2 Traiter vos documents

```powershell
cd d:\iso-doc-navigator-main
python -m ml_core.ingest.batch_processor ./ml_core/data/pdfs ./ml_core/data/chunks ./ml_core/data/index
```

⏱️ **Temps estimé :** 3-5 minutes

**Vous devriez voir :**
```
Found 12 documents to process
Processing: ISO_9001_V_2015_Fr.pdf
✓ Created 150 chunks
...
✓ Building FAISS index...
✓ Index saved to ./ml_core/data/index
```

### 1.3 Vérifier que tout est prêt

```powershell
# Vérifier les chunks
dir ml_core\data\chunks\all_documents_chunks.json

# Vérifier l'index FAISS
dir ml_core\data\index\faiss_index.bin
```

✅ Si ces fichiers existent → Passez à l'étape 2 !

---

## 🎯 ÉTAPE 2 : Lancer le Backend (API ML)

Ouvrez un **NOUVEAU terminal PowerShell** :

```powershell
cd d:\iso-doc-navigator-main\ml_core
uvicorn ml_core.api.api:app --reload --host 0.0.0.0 --port 8000
```

**Vous devriez voir :**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

⏱️ **Premier lancement :** 10-15 minutes (téléchargement LLaMA 3.2 3B)  
⏱️ **Lancements suivants :** 30 secondes

### Tester l'API

Ouvrez votre navigateur : **http://localhost:8000/docs**

Vous devriez voir la documentation Swagger avec les endpoints :
- `POST /ask` - Poser une question
- `POST /ingest` - Ingérer un document
- `GET /info` - Infos système

✅ **Laissez ce terminal OUVERT** - Le backend doit rester actif !

---

## 🎯 ÉTAPE 3 : Lancer le Frontend (Interface React)

Ouvrez un **DEUXIÈME terminal PowerShell** :

```powershell
cd d:\iso-doc-navigator-main\iso-doc-navigator-main
npm install
```

⏱️ **Temps estimé :** 2-3 minutes (première fois uniquement)

Ensuite, créez le fichier de configuration :

```powershell
# Créer .env.local
echo "VITE_ML_API_URL=http://localhost:8000" > .env.local
```

Puis lancez le frontend :

```powershell
npm run dev
```

**Vous devriez voir :**
```
VITE v5.x.x  ready in 500 ms
➜  Local:   http://localhost:5173/
```

✅ **Laissez ce terminal OUVERT aussi !**

---

## 🎯 ÉTAPE 4 : Utiliser le Chatbot

Ouvrez votre navigateur : **http://localhost:5173**

Vous devriez voir votre interface !

### Intégrer le chatbot dans votre interface

Si votre interface React n'a pas encore le composant chatbot, utilisez les hooks que j'ai créés :

```typescript
import { useAskQuestion } from '@/hooks/useMLCore';

function ChatbotComponent() {
  const { mutate: askQuestion, data, isPending } = useAskQuestion();
  
  const handleSubmit = (question: string) => {
    askQuestion({ 
      query: question,
      top_k: 5,
      temperature: 0.7
    });
  };
  
  return (
    <div>
      {isPending && <p>Chargement...</p>}
      {data && (
        <>
          <p><strong>Réponse:</strong> {data.answer}</p>
          <div>
            <strong>Sources:</strong>
            {data.sources.map(s => (
              <div key={s.chunk_id}>
                {s.document} - {s.section} (p.{s.page})
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
```

---

## 🧪 TESTER avec l'API directement

Si vous voulez tester sans l'interface, utilisez curl ou PowerShell :

```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/ask" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"query": "Qu''est-ce que l''ISO 9001?", "top_k": 3}'
```

Ou via le navigateur : http://localhost:8000/docs → Testez `/ask`

---

## 📋 RÉSUMÉ - Ce qui doit tourner

Vous devez avoir **2 terminaux ouverts** :

| Terminal | Commande | URL |
|----------|----------|-----|
| **Terminal 1** | `uvicorn ml_core.api.api:app --reload` | http://localhost:8000 |
| **Terminal 2** | `npm run dev` | http://localhost:5173 |

---

## 🔄 WORKFLOW COMPLET

```
┌─────────────────┐
│ Vous posez une  │
│ question dans   │
│ l'interface     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Frontend React  │ Port 5173
│ (localhost)     │
└────────┬────────┘
         │ HTTP POST
         ▼
┌─────────────────┐
│ Backend FastAPI │ Port 8000
│ ml_core/api     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 1. Embedder     │ → Vectorise la question
│ 2. FAISS Search │ → Trouve docs pertinents
│ 3. LLaMA        │ → Génère la réponse
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Réponse +       │
│ Sources citées  │
└─────────────────┘
```

---

## ⚡ COMMANDES RAPIDES

### Lancer tout d'un coup (Windows)

Créez un fichier `start.bat` à la racine :

```batch
@echo off
start "Backend ML" cmd /k "cd ml_core && uvicorn ml_core.api.api:app --reload"
timeout /t 5
start "Frontend React" cmd /k "cd iso-doc-navigator-main && npm run dev"
echo.
echo Chatbot démarré !
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
```

Double-cliquez sur `start.bat` → Tout démarre !

### Arrêter tout

- `Ctrl+C` dans chaque terminal
- Ou fermez les fenêtres

---

## 🐛 PROBLÈMES COURANTS

### "Module not found: ml_core"
→ Vous n'êtes pas dans le bon dossier  
→ Solution: `cd d:\iso-doc-navigator-main`

### "Port 8000 already in use"
→ Le backend tourne déjà  
→ Solution: Trouvez et fermez l'ancien processus

### "Cannot connect to API"
→ Le backend n'est pas démarré  
→ Solution: Lancez le terminal 1 (API) en premier

### "Out of memory"
→ Fermez les applications inutiles  
→ Le modèle LLaMA 4-bit nécessite ~4-6 GB RAM

### Questions sans réponses
→ L'index n'a pas été créé  
→ Relancez l'étape 1.2 (batch_processor)

---

## ✅ CHECKLIST DE DÉMARRAGE

- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Documents traités (fichier `all_documents_chunks.json` existe)
- [ ] Index FAISS créé (fichier `faiss_index.bin` existe)
- [ ] Terminal 1 : Backend lancé (http://localhost:8000/docs fonctionne)
- [ ] Terminal 2 : Frontend lancé (http://localhost:5173 fonctionne)
- [ ] Fichier `.env.local` créé avec `VITE_ML_API_URL=http://localhost:8000`

---

## 🎯 PROCHAINES ÉTAPES

1. ✅ Lancez le système (étapes 2 et 3)
2. 📝 Testez avec des questions simples
3. 🎨 Personnalisez l'interface React si besoin
4. 🚀 Déployez sur un serveur (optionnel)

**Besoin d'aide ?** Consultez `TEST_GUIDE.md` pour plus de détails !
