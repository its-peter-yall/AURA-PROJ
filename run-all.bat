@echo off
echo Starting AURA Platform (Cloud Redis Mode)...

REM --- REDIS CONFIGURATION ---
set REDIS_HOST=redis-15346.c246.us-east-1-4.ec2.cloud.redislabs.com
set REDIS_PORT=15346
set REDIS_USERNAME=default
set REDIS_PASSWORD=kbFBdbINTaSf2qIHQ6dzMpTLarxi5oN3
set REDIS_DB=0
set REDIS_ENABLED=true

REM Create the full Redis URL for the NOTES-MANAGER (using redis:// without SSL)
set REDIS_URL=redis://%REDIS_USERNAME%:%REDIS_PASSWORD%@%REDIS_HOST%:%REDIS_PORT%/%REDIS_DB%

echo Configured to use Cloud Redis: %REDIS_HOST%:%REDIS_PORT%

echo Starting AURA-CHAT Backend on port 8000...
start "AURA-CHAT Backend" cmd /k "call .venv\Scripts\activate && set REDIS_HOST=%REDIS_HOST% && set REDIS_PORT=%REDIS_PORT% && set REDIS_USERNAME=%REDIS_USERNAME% && set REDIS_PASSWORD=%REDIS_PASSWORD% && set REDIS_DB=%REDIS_DB% && set REDIS_ENABLED=true && cd AURA-CHAT && python -m uvicorn server.main:app --reload --port 8000"

echo Starting AURA-CHAT ARQ Worker for document processing...
start "AURA-CHAT ARQ Worker" cmd /k "call .venv\Scripts\activate && set REDIS_HOST=%REDIS_HOST% && set REDIS_PORT=%REDIS_PORT% && set REDIS_USERNAME=%REDIS_USERNAME% && set REDIS_PASSWORD=%REDIS_PASSWORD% && set REDIS_DB=%REDIS_DB% && set REDIS_ENABLED=true && cd AURA-CHAT && python run_arq_worker.py"

echo Starting AURA-CHAT Frontend on port 5173...
start "AURA-CHAT Frontend" cmd /k "cd AURA-CHAT\client && npm run dev -- --port 5173"

echo Starting AURA-NOTES-MANAGER Backend on port 8001...
start "AURA-NOTES Backend" cmd /k "call .venv\Scripts\activate && set REDIS_URL=%REDIS_URL% && set REDIS_ENABLED=true && cd AURA-NOTES-MANAGER\api && python -m uvicorn main:app --reload --port 8001"

echo Starting Celery Worker for KG Processing...
start "AURA-NOTES Celery" cmd /k "call .venv\Scripts\activate && set REDIS_URL=%REDIS_URL% && set PYTHONPATH=%CD%\AURA-NOTES-MANAGER && cd AURA-NOTES-MANAGER\api && celery -A tasks worker -l info -Q kg_processing -P solo"

echo Starting AURA-NOTES-MANAGER Frontend on port 5174...
start "AURA-NOTES Frontend" cmd /k "cd AURA-NOTES-MANAGER\frontend && npm run dev -- --port 5174"

echo.
echo ============================================
echo   All services started in Cloud Redis mode!
echo ============================================
echo   Redis:        Cloud Redis (%REDIS_HOST%)
echo   AURA-CHAT:    http://127.0.0.1:8000 (API)
echo   AURA-CHAT:    http://127.0.0.1:5173 (Frontend)
echo   AURA-CHAT:    ARQ Worker (document processing)
echo   AURA-NOTES:   http://127.0.0.1:8001 (API)
echo   AURA-NOTES:   http://127.0.0.1:5174 (Frontend)
echo   AURA-NOTES:   Celery Worker (KG processing)
echo ============================================
echo   Note: Close all windows to stop all services
echo ============================================