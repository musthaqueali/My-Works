@echo off
title Restart I LOVE FILES Server - Azure VM
cd /d "%~dp0"

echo ====================================================================
echo   Restarting I LOVE FILES Server on Azure VM
echo ====================================================================
echo.

echo 1. Stopping any currently running Python server instances...
schtasks /end /tn "ILoveFiles_24x7" >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo 2. Verifying CAD Engine (DWG TrueView / AutoCAD)...
python -c "
from converters.autocad_plotter import get_autocad_console_path, is_autocad_available
console = get_autocad_console_path()
if is_autocad_available():
    print('   [SUCCESS] Engine found: ' + str(console))
else:
    print('   [WARNING] accoreconsole.exe not found yet.')
"

echo.
echo 3. Starting the server in the background...
set PORT=8000
if not exist "C:\caddy\Caddyfile" set PORT=80
start "ILoveFiles Server" /B python -m uvicorn app:app --host 0.0.0.0 --port %PORT% --workers 2

timeout /t 3 /nobreak >nul

echo.
echo 4. Registering / updating 24x7 Windows Autostart Task...
schtasks /create /tn "ILoveFiles_24x7" /tr "\"%~dp0run_server_background.bat\"" /sc ONSTART /ru SYSTEM /rl HIGHEST /f >nul 2>&1
if %errorlevel% neq 0 (
    schtasks /create /tn "ILoveFiles_24x7" /tr "\"%~dp0run_server_background.bat\"" /sc ONLOGON /rl HIGHEST /f >nul 2>&1
)

echo.
echo ======================================================================
echo   SUCCESS: Server is RESTARTED and RUNNING!
echo ======================================================================
echo You can check the live engine status anytime by visiting:
echo https://ilovefiles.southindia.cloudapp.azure.com/api/cad/engine-status
echo.
pause
