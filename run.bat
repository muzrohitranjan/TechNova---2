@echo off
echo ========================================
echo Tech Nova - Starting Backend & Frontend
echo ========================================

REM Create virtual environment if not exists (use .venv folder)
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Install dependencies
echo Installing dependencies...
call .venv\Scripts\pip install -r requirements.txt

REM Start backend server in background
echo Starting Backend Server...
start "Backend Server" cmd /k "call .venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend (simple HTTP server)
echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd working-frontend && python -m http.server 3000"

echo.
echo ========================================
echo Servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo ========================================
echo Press any key to exit (servers will keep running)...
pause >nul

