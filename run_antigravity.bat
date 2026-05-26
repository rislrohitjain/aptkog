@echo off
title Antigravity 2.0 Launcher
echo ===================================================
echo ⚡ Starting Antigravity 2.0 Setup and Launcher
echo ===================================================
cd /d "%~dp0"

:: 1. Check for virtual environment
if not exist venv (
    echo [INFO] Virtual environment 'venv' not found. Creating it...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. Ensure Python is installed and in PATH.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created.
)

:: 2. Upgrade pip and install requirements
echo [INFO] Installing/Verifying dependencies...
call venv\Scripts\python.exe -m pip install --upgrade pip
call venv\Scripts\pip.exe install -r backend/Requirements.txt
call venv\Scripts\pip.exe install -r frontend/requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies. Check network connection or requirements files.
    pause
    exit /b 1
)
echo [SUCCESS] Dependencies installed successfully.

:: 2.5. Update environment IP address config
echo [INFO] Detecting current local IP and updating configurations...
call venv\Scripts\python.exe update_ip.py

:: Read updated HOST from backend/.env
set APP_HOST=127.0.0.1
if exist backend\.env (
    for /f "usebackq tokens=1,2 delims==" %%i in ("backend\.env") do (
        if "%%i"=="HOST" set APP_HOST=%%j
    )
)

:: 3. Launch Backend in a new window
echo [INFO] Launching Backend API server (FastAPI)...
start "Antigravity 2.0 Backend" cmd /k "call venv\Scripts\activate && uvicorn backend.app.main:app --host %APP_HOST% --port 8000"

:: 4. Launch Frontend in a new window
echo [INFO] Launching Frontend UI server (Streamlit)...
start "Antigravity 2.0 Frontend" cmd /k "call venv\Scripts\activate && streamlit run frontend/app.py --server.port 8501 --server.address %APP_HOST%"

echo ===================================================
echo 🚀 Launch commands executed.
echo    - Backend URL: http://%APP_HOST%:8000
echo    - Frontend URL: http://%APP_HOST%:8501
echo ===================================================
