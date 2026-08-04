@echo off
echo Starting JARVIS AI Operating System...
echo.

REM Start backend
echo Starting backend service...
start "JARVIS Backend" cmd /k "cd backend && venv\Scripts\activate && python main.py"

REM Wait a moment for backend to start
timeout /t 5 >nul

REM Start frontend
echo Starting frontend service...
start "JARVIS Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both services have been started.
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:3000
echo.
echo Press any close this window to stop the services.
pause >nul