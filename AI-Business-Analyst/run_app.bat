@echo off
title AI Business Analyst Platform
cd /d "%~dp0"
echo ===================================================
echo   AI BUSINESS ANALYST PLATFORM
echo   Starting Enterprise Decision & Analytics Server...
echo ===================================================

set PORT=8085
start "" http://localhost:8085

python -m uvicorn backend.server:app --host 0.0.0.0 --port 8085 --reload

pause
