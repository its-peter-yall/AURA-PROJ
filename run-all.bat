@echo off
echo Starting AURA Platform...

echo Stopping any process on port 6379...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :6379 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)

echo Restarting Redis (WSL) on port 6379...
REM Start Redis directly in WSL (no sudo needed for redis-server)
wsl -d Ubuntu -- bash -c "pkill redis-server 2>/dev/null; redis-server --daemonize yes --port 6379" 2>nul || wsl -- bash -c "pkill redis-server 2>/dev/null; redis-server --daemonize yes --port 6379" 2>nul

echo Waiting for Redis to be ready...

REM Verify Redis is running (max 10 attempts)
set redis_failed=1
for /L %%i in (1,1,10) do (
    wsl -d Ubuntu -- bash -c "redis-cli ping" 2>nul | findstr /C:"PONG" >nul
    if not errorlevel 1 set redis_failed=0 & goto :redis_ready
    timeout /t 1 /nobreak >nul
)
:redis_ready
if %redis_failed%==0 (
    echo Redis started successfully!
) else (
    echo ERROR: Redis failed to start after 10 attempts. Check WSL and Redis installation.
)

REM Use 127.0.0.1 for Redis connection
set REDIS_HOST=127.0.0.1
set REDIS_PORT=6379
set REDIS_DB=0
set REDIS_ENABLED=true

echo Starting AURA-CHAT Backend on port 8000...
start "AURA-CHAT Backend" cmd /k "call .venv\Scripts\activate && set REDIS_HOST=127.0.0.1 && set REDIS_PORT=6379 && set REDIS_DB=0 && set REDIS_ENABLED=true && cd AURA-CHAT && python -m uvicorn server.main:app --reload --port 8000"

echo Starting AURA-CHAT ARQ Worker for document processing...
start "AURA-CHAT ARQ Worker" cmd /k "call .venv\Scripts\activate && set REDIS_HOST=127.0.0.1 && set REDIS_PORT=6379 && set REDIS_DB=0 && set REDIS_ENABLED=true && cd AURA-CHAT && python run_arq_worker.py"

echo Starting AURA-CHAT Frontend on port 5173...
start "AURA-CHAT Frontend" cmd /k "cd AURA-CHAT\client && npm run dev -- --port 5173"

echo Starting AURA-NOTES-MANAGER Backend on port 8001...
start "AURA-NOTES Backend" cmd /k "call .venv\Scripts\activate && set REDIS_HOST=127.0.0.1 && set REDIS_PORT=6379 && set REDIS_DB=0 && set REDIS_ENABLED=true && cd AURA-NOTES-MANAGER\api && python -m uvicorn main:app --reload --port 8001"

echo Starting Celery Worker for KG Processing...
start "AURA-NOTES Celery" cmd /k "call .venv\Scripts\activate && set REDIS_HOST=127.0.0.1 && set REDIS_PORT=6379 && set REDIS_DB=0 && set REDIS_ENABLED=true && set PYTHONPATH=D:\Peter\AURA Twin Proj\AURA-PROJ\AURA-NOTES-MANAGER && cd AURA-NOTES-MANAGER\api && celery -A tasks worker -l info -Q kg_processing -P solo"

echo Starting AURA-NOTES-MANAGER Frontend on port 5174...
start "AURA-NOTES Frontend" cmd /k "cd AURA-NOTES-MANAGER\frontend && npm run dev -- --port 5174"

echo.
echo ============================================
echo   All services started!
echo ============================================
echo   Redis:        WSL Redis on port 6379 (Background)
echo   AURA-CHAT:    http://127.0.0.1:8000 (API)
echo   AURA-CHAT:    http://127.0.0.1:5173 (Frontend)
echo   AURA-CHAT:    ARQ Worker (document processing)
echo   AURA-NOTES:   http://127.0.0.1:8001 (API)
echo   AURA-NOTES:   http://127.0.0.1:5174 (Frontend)
echo   AURA-NOTES:   Celery Worker (KG processing)
echo ============================================
echo   Note: Close all windows to stop all services
echo ============================================