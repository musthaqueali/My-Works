@echo off
echo ===================================================
echo   Starting The AI Dispatch - Newsletter Studio
echo ===================================================
echo Opening web interface at: http://127.0.0.1:8000
echo.
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
