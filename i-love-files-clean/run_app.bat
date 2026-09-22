@echo off
title I LOVE FILES - Local Server
cd /d %~dp0

echo ========================================================
echo   I LOVE FILES - Local Server
echo   Starting backend at http://localhost:8000
echo ========================================================

echo Opening browser at http://localhost:8000...
start http://localhost:8000

python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
pause

