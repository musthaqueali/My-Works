@echo off
title I LOVE FILES - Local AutoCAD Native Server
cd /d %~dp0

echo ========================================================
echo   Starting I LOVE FILES on Local Machine
echo   AutoCAD 2026 Engine: ACTIVE
echo ========================================================

echo Opening browser...
start http://localhost:8000

echo Starting FastAPI server on http://localhost:8000...
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
pause
