@echo off
title Setup Native AutoCAD / DWG TrueView Engine - I LOVE FILES
cd /d "%~dp0"

echo ========================================================================
echo   I LOVE FILES - Native AutoCAD / DWG TrueView Engine Setup (Azure VM)
echo ========================================================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in the system PATH!
    echo Please ensure Python is installed and added to PATH on this machine.
    echo.
    pause
    exit /b 1
)

python "%~dp0setup_autocad_engine.py"

if %errorlevel% neq 0 (
    echo.
    echo [NOTICE] Setup finished with exit code %errorlevel%.
)

echo.
pause
