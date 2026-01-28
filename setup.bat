@echo off
setlocal enabledelayedexpansion

echo ==============================================================
echo              AURA Monorepo Setup Script
echo ==============================================================
echo.

REM Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Found Python version: !PYTHON_VERSION!

REM Check if Node.js is installed
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Node.js is not installed. Frontend setup will be skipped.
    echo Install Node.js from https://nodejs.org/
    set SKIP_FRONTEND=1
) else (
    for /f "tokens=1" %%i in ('node --version') do set NODE_VERSION=%%i
    echo [INFO] Found Node.js version: !NODE_VERSION!
    set SKIP_FRONTEND=0
)

echo.
echo ==============================================================
echo  Step 1: Creating Python Virtual Environment
echo ==============================================================
echo.

if not exist ".venv" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
)

if not exist ".venv\\Scripts\activate.bat" (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo [SUCCESS] Virtual environment ready.

echo.
echo ==============================================================
echo  Step 2: Installing Python Dependencies
echo ==============================================================
echo.

call .venv\\Scripts\activate.bat

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip --quiet

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found at repo root.
    pause
    exit /b 1
)

echo [INFO] Installing dependencies from requirements.txt...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install some Python dependencies.
    pause
    exit /b 1
)

echo [SUCCESS] Python dependencies installed.

echo.
echo ==============================================================
echo  Step 3: Installing Frontend Dependencies
echo ==============================================================
echo.

if "!SKIP_FRONTEND!"=="1" (
    echo [SKIPPED] Node.js not found. Install Node.js and rerun this script.
) else (
    if exist "AURA-CHAT\client\package.json" (
        echo [INFO] Installing AURA-CHAT frontend packages...
        pushd AURA-CHAT\client
        npm install
        if %errorlevel% neq 0 (
            echo [ERROR] Failed to install AURA-CHAT frontend packages.
            popd
            pause
            exit /b 1
        )
        popd
        echo [SUCCESS] AURA-CHAT frontend dependencies installed.
    ) else (
        echo [WARNING] AURA-CHAT\client\package.json not found. Skipping.
    )

    if exist "AURA-NOTES-MANAGER\frontend\package.json" (
        echo [INFO] Installing AURA-NOTES-MANAGER frontend packages...
        pushd AURA-NOTES-MANAGER\frontend
        npm install
        if %errorlevel% neq 0 (
            echo [ERROR] Failed to install AURA-NOTES-MANAGER frontend packages.
            popd
            pause
            exit /b 1
        )
        popd
        echo [SUCCESS] AURA-NOTES-MANAGER frontend dependencies installed.
    ) else (
        echo [WARNING] AURA-NOTES-MANAGER\frontend\package.json not found. Skipping.
    )

    if exist "AURA-NOTES-MANAGER\package.json" (
        echo [INFO] Installing AURA-NOTES-MANAGER root packages...
        pushd AURA-NOTES-MANAGER
        npm install
        if %errorlevel% neq 0 (
            echo [ERROR] Failed to install AURA-NOTES-MANAGER root packages.
            popd
            pause
            exit /b 1
        )
        popd
        echo [SUCCESS] AURA-NOTES-MANAGER root dependencies installed.
    ) else (
        echo [WARNING] AURA-NOTES-MANAGER\package.json not found. Skipping.
    )
)

echo.
echo ==============================================================
echo  Step 4: Environment Files
echo ==============================================================
echo.

if not exist "AURA-CHAT\.env" (
    if exist "AURA-CHAT\.env.example" (
        copy "AURA-CHAT\.env.example" "AURA-CHAT\.env" >nul
        echo [INFO] Created AURA-CHAT\.env from template.
    ) else (
        echo [WARNING] AURA-CHAT\.env.example not found.
    )
) else (
    echo [INFO] AURA-CHAT\.env already exists.
)

if not exist "AURA-NOTES-MANAGER\.env" (
    if exist "AURA-NOTES-MANAGER\.env.template" (
        copy "AURA-NOTES-MANAGER\.env.template" "AURA-NOTES-MANAGER\.env" >nul
        echo [INFO] Created AURA-NOTES-MANAGER\.env from template.
    ) else (
        echo [WARNING] AURA-NOTES-MANAGER\.env.template not found.
    )
) else (
    echo [INFO] AURA-NOTES-MANAGER\.env already exists.
)

echo.
echo ==============================================================
echo  Setup Complete
echo ==============================================================
echo.
echo Next steps:
echo  1. Update the .env files with your credentials.
echo  2. Start all services: run-all.bat
echo.
pause
