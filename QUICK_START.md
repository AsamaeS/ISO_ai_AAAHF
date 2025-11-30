# 🎯 DÉMARRAGE RAPIDE - 3 Étapes Seulement

## ✅ Prérequis (vous avez déjà)
- Python 3.10+
- Node.js
- Connexion internet

---

## 📦 ÉTAPE 1 : Installation (5 minutes)

Ouvrez PowerShell et exécutez :

```powershell
cd d:\iso-doc-navigator-main\ml_core

# Installer TOUTES les dépendances Python
pip install -r requirements.txt
pip install python-docx openpyxl xlrd
```

✅ **C'est tout pour Python !**

Puis pour le frontend :

```powershell
cd ..\iso-doc-navigator-main
npm install
echo VITE_ML_API_URL=http://localhost:8000 > .env.local
```

✅ **C'est tout pour Node !**

---

## 📄 ÉTAPE 2 : Traiter vos documents (3-5 minutes)

```powershell
cd d:\iso-doc-navigator-main
python -m ml_core.ingest.batch_processor ./ml_core/data/pdfs ./ml_core/data/chunks ./ml_core/data/index
```

**Vous verrez :**
- Reading PDFs, Word, Excel...
- Creating chunks...
- Generating embeddings...
- Building FAISS index...

✅ **Terminé !** Index créé dans `ml_core/data/index/`

---

## 🚀 ÉTAPE 3 : Lancer le chatbot (2 terminaux)

### Terminal 1 - Backend (API ML)

```powershell
cd d:\iso-doc-navigator-main\ml_core
uvicorn ml_core.api.api:app --reload
```

**🕒 Premier lancement :** 10-15 min (télécharge LLaMA 3 GB)  
**🕒 Lancements suivants :** 30 secondes

**Vous verrez :**
```
Downloading meta-llama/Llama-3.2-3B-Instruct...
Model loaded successfully!
Uvicorn running on http://0.0.0.0:8000
```

✅ **Ne fermez PAS ce terminal !**

### Terminal 2 - Frontend (Interface)

```powershell
cd d:\iso-doc-navigator-main\iso-doc-navigator-main
npm run dev
```

**Vous verrez :**
```
VITE ready in 500 ms
Local: http://localhost:5173/
```

✅ **Ne fermez PAS ce terminal non plus !**

---

## 🎉 C'EST PRÊT !

Ouvrez dans votre navigateur :
- 🌐 **Chatbot :** http://localhost:5173
- 📚 **API docs :** http://localhost:8000/docs

---

## ❓ Questions fréquentes

**Q: LLaMA se télécharge où ?**  
R: Automatiquement dans `C:\Users\hp\.cache\huggingface\hub\`

**Q: Je dois télécharger LLaMA manuellement ?**  
R: **NON**, c'est automatique au premier lancement !

**Q: Ça prend combien d'espace ?**  
R: ~4 GB total (3 GB LLaMA + 1 GB dépendances)

**Q: Combien de temps pour le premier lancement ?**  
R: 15-20 minutes (téléchargement + chargement modèle)

**Q: Et les fois suivantes ?**  
R: 30 secondes (modèle déjà téléchargé)

---

## 🔄 Pour relancer le chatbot (après installation)

**Option rapide :** Double-cliquez sur `start.bat`

**Ou manuellement :**
1. Terminal 1: `uvicorn ml_core.api.api:app --reload`
2. Terminal 2: `npm run dev`

---

**📖 Plus de détails ?** Consultez `DEPENDANCES.md` et `LANCEMENT.md`
