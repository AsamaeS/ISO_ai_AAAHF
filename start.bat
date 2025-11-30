@echo off
REM ============================================================
REM   Démarrage automatique du Chatbot ISO Navigator
REM ============================================================

echo.
echo ========================================
echo   ISO DOCUMENT NAVIGATOR - STARTUP
echo ========================================
echo.

REM Vérifier si l'index existe
if not exist "ml_core\data\index\faiss_index.bin" (
    echo [ERREUR] Index FAISS non trouvé !
    echo.
    echo Vous devez d'abord traiter vos documents :
    echo   cd ml_core
    echo   python -m ml_core.ingest.batch_processor ./data/pdfs ./data/chunks ./data/index
    echo.
    pause
    exit /b 1
)

echo [OK] Index FAISS trouvé
echo.

REM Lancer le backend
echo [1/2] Démarrage du Backend ML (FastAPI)...
echo       Port: 8000
start "ML Core Backend" cmd /k "cd ml_core && uvicorn ml_core.api.api:app --reload --host 0.0.0.0 --port 8000"

echo       Attente du démarrage...
timeout /t 10 /nobreak >nul

REM Lancer le frontend
echo.
echo [2/2] Démarrage du Frontend (React)...
echo       Port: 5173
start "React Frontend" cmd /k "cd iso-doc-navigator-main && npm run dev"

echo.
echo ========================================
echo   CHATBOT DÉMARRÉ !
echo ========================================
echo.
echo   Backend API:  http://localhost:8000
echo   Swagger Docs: http://localhost:8000/docs
echo   Frontend:     http://localhost:5173
echo.
echo   Appuyez sur une touche pour arrêter...
echo ========================================

pause >nul

REM Arrêter les services
echo.
echo Arrêt des services...
taskkill /FI "WindowTitle eq ML Core Backend*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq React Frontend*" /T /F >nul 2>&1

echo Services arrêtés.
pause
