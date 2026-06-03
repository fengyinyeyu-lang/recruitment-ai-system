@echo off
echo Starting Backend (FastAPI)...
start "Recruitment AI Backend" cmd /k "D:\miniconda3\envs\nlp\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"

echo Starting Frontend (Vue 3 + Vite)...
start "Recruitment AI Frontend" cmd /k "cd frontend && npm run dev -- --open"

echo.
echo ===================================================
echo   Services started!
echo   - Backend: http://127.0.0.1:8000
echo   - Frontend: http://localhost:3000
echo ===================================================
echo.
pause
