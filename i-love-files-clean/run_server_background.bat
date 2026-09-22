@echo off
cd /d "%~dp0"
set PORT=8000
if not exist "C:\caddy\Caddyfile" set PORT=80
if not "%~1"=="" set PORT=%1

echo [%date% %time%] Starting server on port %PORT%... >> "%~dp0server.log"
python -m uvicorn app:app --host 0.0.0.0 --port %PORT% --workers 2 >> "%~dp0server.log" 2>&1
