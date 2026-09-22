@echo off
setlocal EnableDelayedExpansion
title Setup 24/7 Autostart Service - I LOVE FILES
cd /d "%~dp0"

echo ====================================================================
echo   I LOVE FILES - 24/7 Background Service Setup
echo ====================================================================
echo.

:: 1. Verify files are properly extracted
if not exist "%~dp0app.py" (
    echo [ERROR] You are running this script directly from INSIDE the zip file!
    echo.
    echo Please EXTRACT the zip file first:
    echo  1. Right-click the zip file -^> "Extract All..."
    echo  2. Extract to C:\i-love-files
    echo  3. Run this script from the extracted folder.
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0run_server_background.bat" (
    echo [ERROR] run_server_background.bat not found in %~dp0
    echo.
    pause
    exit /b 1
)

:: 2. Check Administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [NOTICE] Running without elevated Administrator privileges.
    echo If registering the task fails, please:
    echo Right-click setup_24x7_autostart.bat and choose "Run as administrator"
    echo.
)

:: 3. Stop any existing task
echo Stopping previous task if running...
schtasks /end /tn "ILoveFiles_24x7" >nul 2>&1
schtasks /delete /tn "ILoveFiles_24x7" /f >nul 2>&1

:: 4. Create Windows Task
echo Registering Windows Task: ILoveFiles_24x7...
schtasks /create /tn "ILoveFiles_24x7" /tr "\"%~dp0run_server_background.bat\"" /sc ONSTART /ru SYSTEM /rl HIGHEST /f >nul 2>&1

if %errorlevel% neq 0 (
    echo [!] Registering as SYSTEM failed. Registering for current user at logon...
    schtasks /create /tn "ILoveFiles_24x7" /tr "\"%~dp0run_server_background.bat\"" /sc ONLOGON /rl HIGHEST /f >nul 2>&1
)

if %errorlevel% neq 0 (
    echo [!] Elevated task failed. Registering standard user logon task...
    schtasks /create /tn "ILoveFiles_24x7" /tr "\"%~dp0run_server_background.bat\"" /sc ONLOGON /f >nul 2>&1
)

echo Starting the 24x7 service now...
schtasks /run /tn "ILoveFiles_24x7"

echo.
echo ======================================================================
echo   SUCCESS: 24/7 Background Service is Configured and Triggered!
echo ======================================================================
echo - You can now safely CLOSE your Remote Desktop session.
echo - The Azure server will keep running 24x7!
echo - To check server logs anytime, open: "%~dp0server.log"
echo ======================================================================
echo.
pause
