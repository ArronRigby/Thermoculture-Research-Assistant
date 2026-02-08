@echo off
TITLE Thermoculture Research Assistant Control Panel
echo ==========================================================
echo   Starting Thermoculture Research Assistant
echo ==========================================================
echo.

:: Start Backend
echo [1/2] Starting Backend Server (Port 8000)...
start "TRA Backend" cmd /k "cd backend && venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

:: Wait a moment for backend to initialize
timeout /t 2 /nobreak > nul

:: Start Frontend
echo [2/2] Starting Frontend Server (Port 5173)...
start "TRA Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================================
echo   Both servers are starting in separate windows.
echo.
echo   - Backend API: http://localhost:8000/docs
echo   - Frontend:    http://localhost:5173
echo.
echo   Close the separate windows to stop the servers.
echo ==========================================================
pause
