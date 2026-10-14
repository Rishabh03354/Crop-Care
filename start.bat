@echo off
echo ==============================================
echo       Starting Crop Care (Group DS-22)
echo ==============================================

echo [1/2] Starting FastAPI Backend on port 8000...
start "Crop Care Backend" cmd /k "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo [2/2] Starting Next.js Frontend on port 3000...
start "Crop Care Frontend" cmd /k "cd frontend && npm run dev"

echo Waiting for servers to initialize...
timeout /t 3 /nobreak >nul

echo Opening browser at http://localhost:3000...
start http://localhost:3000

echo Done! Both servers are running.
