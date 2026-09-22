@echo off
title I LOVE FILES - Cloud Server Backend
cd /d "%~dp0"

echo ========================================================
echo   Starting I LOVE FILES Backend (24x7 Ready)
echo ========================================================

set PORT=80
if exist "C:\caddy\Caddyfile" set PORT=8000
if not "%~1"=="" set PORT=%1

echo Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH! Please install Python 3.10+ and check 'Add to PATH'.
    pause
    exit /b 1
)

echo Checking and installing required packages (python-docx, pdf2docx, etc.)...
python -m pip install -r requirements.txt --quiet

echo Starting FastAPI Server on http://0.0.0.0:%PORT%...
python -m uvicorn app:app --host 0.0.0.0 --port %PORT% --workers 2
pause

