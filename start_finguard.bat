@echo off
title FinGuard Enterprise Launcher
echo ========================================================
echo   FinGuard - Autonomous Financial Risk Intelligence
echo   Enterprise 9-Layer Architecture Launcher
echo ========================================================
echo.

echo [1/3] Starting Backend (FastAPI on Port 8000)...
start "FinGuard Backend (FastAPI)" cmd /k "python backend/main.py"

echo [2/3] Starting Frontend (Vite on Port 5173)...
start "FinGuard Frontend (React + Vite)" cmd /k "cd frontend && npm run dev"

echo [3/3] Waiting for servers to initialize...
timeout /t 4 /nobreak >nul

echo Opening FinGuard UI in your default browser...
start http://localhost:5173

echo.
echo ========================================================
echo   FinGuard is running!
echo   Frontend UI:      http://localhost:5173
echo   Backend API Docs: http://127.0.0.1:8000/docs
echo   Health Endpoint:  http://127.0.0.1:8000/health
echo.
echo   Demo Login Accounts:
echo   - Administrator:  admin@finguard.local  / 123456
echo   - Investigator:   user@finguard.local   / 12345
echo ========================================================
echo.
pause

