@echo off
REM ============================================================
REM   PREMIÈRE INSTALLATION - ISO Document Navigator
REM   Exécutez ce script UNE SEULE FOIS pour tout configurer
REM ============================================================

echo.
echo ========================================
echo   INSTALLATION COMPLÈTE
echo ========================================
echo.

REM Étape 1 : Installer les dépendances Python
echo [1/3] Installation des dépendances Python...
cd ml_core
python -m pip install -r requirements.txt
python -m pip install python-docx openpyxl xlrd

if errorlevel 1 (
    echo [ERREUR] Installation Python échouée
    pause
    exit /b 1
)

echo [OK] Dépendances Python installées
cd ..

REM Étape 2 : Installer les dépendances Node
echo.
echo [2/3] Installation des dépendances Node.js...
cd iso-doc-navigator-main
call npm install

if errorlevel 1 (
    echo [ERREUR] Installation npm échouée
    pause
    exit /b 1
)

REM Créer .env.local
echo VITE_ML_API_URL=http://localhost:8000 > .env.local
echo [OK] Configuration frontend créée

cd ..

REM Étape 3 : Traiter les documents
echo.
echo [3/3] Traitement des documents...
echo (Cela peut prendre 5-10 minutes)
python -m ml_core.ingest.batch_processor ./ml_core/data/pdfs ./ml_core/data/chunks ./ml_core/data/index

if errorlevel 1 (
    echo [ERREUR] Traitement des documents échoué
    pause
    exit /b 1
)

REM Terminé
echo.
echo ========================================
echo   INSTALLATION TERMINÉE !
echo ========================================
echo.
echo Prochaines étapes :
echo   1. Double-cliquez sur start.bat
echo   2. Ouvrez http://localhost:5173
echo   3. Posez vos questions sur les normes ISO !
echo.
echo ========================================
pause
