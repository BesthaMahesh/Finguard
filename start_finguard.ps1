# FinGuard Enterprise One-Click PowerShell Launcher
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  FinGuard - Autonomous Financial Risk Intelligence     " -ForegroundColor Cyan
Write-Host "  Enterprise 9-Layer Architecture Launcher              " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Launching FastAPI Backend on Port 8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python backend/main.py"

Write-Host "[2/3] Launching React Vite Frontend on Port 5173..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location frontend; npm run dev"

Write-Host "[3/3] Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 4

Write-Host "Opening FinGuard in browser..." -ForegroundColor Green
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  FinGuard is running!" -ForegroundColor Green
Write-Host "  Frontend:    http://localhost:5173" -ForegroundColor White
Write-Host "  Backend API: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  Admin Login: admin@finguard.local / 123456" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Green

