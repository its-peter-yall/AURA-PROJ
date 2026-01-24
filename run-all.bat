@echo off
echo Starting AURA Platform...

echo Stopping any existing Redis instances...
wsl sudo pkill redis-server 2>nul
timeout /t 2 /nobreak >nul

echo Starting Redis (WSL) on port 6379...
start "Redis Server" cmd /k "wsl sudo redis-server --bind 0.0.0.0 --daemonize no"

echo Waiting for Redis to be ready...
timeout /t 3 /nobreak >nul

REM Use 127.0.0.1 for Redis connection
set REDIS_HOST=127.0.0.1
set REDIS_PORT=6379
set REDIS_DB=0
set REDIS_ENABLED=true

echo Starting AURA-CHAT Backend on port 8000...
start "AURA-CHAT Backend" cmd /k "call venv\Scripts\activate && set REDIS_HOST=127.0.0.1 && set REDIS_PORT=6379 && set REDIS_DB=0 && set REDIS_ENABLED=true && cd AURA-CHAT && python -m uvicorn server.main:app --reload --port 8000"

echo Starting AURA-CHAT Frontend on port 5173...
start "AURA-CHAT Frontend" cmd /k "cd AURA-CHAT\client && npm run dev -- --port 5173"

echo Starting AURA-NOTES-MANAGER Backend on port 8001...
start "AURA-NOTES Backend" cmd /k "call venv\Scripts\activate && set REDIS_HOST=127.0.0.1 && set REDIS_PORT=6379 && set REDIS_DB=0 && set REDIS_ENABLED=true && cd AURA-NOTES-MANAGER\api && python -m uvicorn main:app --reload --port 8001"

echo Starting Celery Worker for KG Processing...
start "AURA-NOTES Celery" cmd /k "call venv\Scripts\activate && set REDIS_HOST=127.0.0.1 && set REDIS_PORT=6379 && set REDIS_DB=0 && set REDIS_ENABLED=true && cd AURA-NOTES-MANAGER\api && celery -A tasks worker -l info -Q kg_processing -P solo"

echo Starting AURA-NOTES-MANAGER Frontend on port 5174...
start "AURA-NOTES Frontend" cmd /k "cd AURA-NOTES-MANAGER\frontend && npm run dev -- --port 5174"

echo.
echo ============================================
echo   All services started!
echo ============================================
echo   Redis:        WSL Redis on port 6379
echo   AURA-CHAT:    http://127.0.0.1:8000 (API)
echo   AURA-CHAT:    http://127.0.0.1:5173 (Frontend)
echo   AURA-NOTES:   http://127.0.0.1:8001 (API)
echo   AURA-NOTES:   http://127.0.0.1:5174 (Frontend)
echo ============================================
echo   Note: Close all windows to stop all services
echo ============================================
