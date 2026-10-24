@echo off
title AI StudySense Launcher
echo ========================================================
echo        Starting AI StudySense (Backend + Frontend)
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000...
start "AI StudySense Backend" cmd /k ""%~dp0.venv\Scripts\python.exe" -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"

echo [2/2] Starting React Frontend on http://localhost:5173...
cd frontend
start "AI StudySense Frontend" cmd /k "npm run dev"

echo.
echo AI StudySense is starting!
echo Backend:  http://127.0.0.1:8000/docs
echo Frontend: http://localhost:5173
echo ========================================================
