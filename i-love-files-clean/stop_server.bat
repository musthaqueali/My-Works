@echo off
title Stop 24/7 Server - I LOVE FILES
cd /d %~dp0
echo Stopping I LOVE FILES background service...
schtasks /end /tn "ILoveFiles_24x7" >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
echo Server stopped successfully.
pause
