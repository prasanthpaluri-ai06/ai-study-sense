# AI StudySense Local Server Launcher (PowerShell)
$rootDir = $PSScriptRoot
Set-Location $rootDir

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       Starting AI StudySense (Backend + Frontend)      " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Start Backend in separate window
Write-Host "[1/2] Launching FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir'; & '$rootDir\.venv\Scripts\python.exe' -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"

# 2. Start Frontend in separate window
Write-Host "[2/2] Launching React Frontend on http://localhost:5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\frontend'; npm run dev"

Write-Host ""
Write-Host "Servers launched successfully!" -ForegroundColor Yellow
Write-Host "Backend API:  http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host "Frontend App: http://localhost:5173" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
