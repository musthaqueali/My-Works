@echo off
title 100 Days of Machine Learning - Broadsheet Learning Portal
echo =====================================================================
echo   THE 100 DAYS OF MACHINE LEARNING DISPATCH
echo =====================================================================
echo.
echo Launching editorial learning portal...
echo.

python --version >nul 2>&1
if %errorlevel% equ 0 (
    python serve.py
) else (
    echo Python not found in PATH. Opening index.html directly...
    start "" "%~dp0index.html"
    pause
)
