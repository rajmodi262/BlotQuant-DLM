@echo off
title BlotQuant DLM - Starting...
color 0A

echo.
echo  ====================================================
echo    BlotQuant - Deep Learning Western Blot Quantifier
echo  ====================================================
echo.

:: Get the directory where this script lives
cd /d "%~dp0"

:: -------------------------------------------------------
:: 1. Check Python
:: -------------------------------------------------------
echo [1/5] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Python is not installed or not in PATH.
    echo  Download it from https://www.python.org/downloads/
    echo  IMPORTANT: Check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo        Found Python %%i
echo.

:: -------------------------------------------------------
:: 2. Check Node.js
:: -------------------------------------------------------
echo [2/5] Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Node.js is not installed or not in PATH.
    echo  Download it from https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f %%i in ('node --version 2^>^&1') do echo        Found Node.js %%i
echo.

:: -------------------------------------------------------
:: 3. Install Python dependencies
:: -------------------------------------------------------
echo [3/5] Installing Python dependencies...
pip install -r backend\requirements.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  WARNING: Some Python packages may have failed. Trying with --user flag...
    pip install -r backend\requirements.txt --quiet --user --disable-pip-version-check
)
echo        Done.
echo.

:: -------------------------------------------------------
:: 4. Install Node.js dependencies
:: -------------------------------------------------------
echo [4/5] Installing frontend dependencies...
if not exist "frontend\node_modules" (
    cd frontend
    call npm install --silent 2>nul
    cd ..
    echo        Done.
) else (
    echo        Already installed. Skipping.
)
echo.

:: -------------------------------------------------------
:: 5. Start servers
:: -------------------------------------------------------
echo [5/5] Starting BlotQuant...
echo.
echo  Backend:  http://localhost:8001
echo  Frontend: http://localhost:5174
echo.
echo  ====================================================
echo    READY! Opening browser in 5 seconds...
echo    Press Ctrl+C in this window to stop the servers.
echo  ====================================================
echo.

:: Start backend in background
start "BlotQuant Backend" /min cmd /c "cd /d "%~dp0" && python -m uvicorn backend.server:app --host 0.0.0.0 --port 8001 --reload"

:: Wait for backend to boot
timeout /t 3 /nobreak >nul

:: Start frontend in background
start "BlotQuant Frontend" /min cmd /c "cd /d "%~dp0\frontend" && npx vite --host --port 5174"

:: Wait for frontend to boot
timeout /t 4 /nobreak >nul

:: Open browser
start http://localhost:5174

echo  Servers are running. Close this window to stop everything.
echo.
pause
:: Kill child processes when user presses a key
taskkill /fi "WINDOWTITLE eq BlotQuant Backend" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq BlotQuant Frontend" /f >nul 2>&1
