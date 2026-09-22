@echo off
title DamageMech AI - API 571 Threat Screening & DWG Location Mapper
echo ===============================================================================
echo     DamageMech AI: API 571 Corrosion Threat Screening & DWG Location Mapper
echo           Chevron Pasadena Refinery Spec / Pinnacle Solutions
echo ===============================================================================
echo.
echo [1/2] Starting DamageMech Local Python Server on Port 8085...
start /B python damagemech_server.py
timeout /t 2 /nobreak >nul
echo.
echo [2/2] Launching Web Application in Default Browser...
start http://localhost:8085/damagemech_app.html
echo.
echo [SUCCESS] DamageMech AI is running! Keep this window open.
echo To stop the server, close this command window.
pause
