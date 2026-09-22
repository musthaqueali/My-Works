@echo off
setlocal enabledelayedexpansion
title I LOVE FILES - 1-Click Free SSL Setup

echo ==========================================================
echo   I LOVE FILES - Automatic Free SSL Certificate Setup
echo   (Powered by Caddy & Let's Encrypt - 100% Free Forever)
echo ==========================================================
echo.

echo Enter your domain name (example: ilovefiles.centralindia.cloudapp.azure.com)
set /p DOMAIN="Domain: "
Call :norm_domain
if "!DOMAIN!"=="" (
    echo [ERROR] Domain cannot be empty!
    pause
    exit /b 1
)

echo.
echo [*] Target Domain: !DOMAIN!
echo [*] Creating C:\caddy directory...

if not exist "C:\caddy" mkdir "C:\caddy"

if not exist "C:\caddy\caddy.exe" (
    echo [*] Downloading Caddy Windows 64-bit engine...
    curl.exe -L -websockets -o "C:\caddy\caddy.zip" "https://github.com/caddyserver/caddy/releases/download/v2.9.1/caddy_2.9.1_windows_amd64.zip"
    if exist "C:\caddy\caddy.zip" (
        echo [*] Extracting caddy.exe...
        powershell -Command "Expand-Archive -Path 'C:\caddy\caddy.zip' -DestinationPath 'C:\caddy' -Force"
        del "C:\caddy\caddy.zip"
    )
)

if not exist "C:\caddy\caddy.exe" (
    echo [ERROR] Could not auto-download caddy.exe.
    echo Please download manually from https://caddyserver.com/download and place in C:\caddy\caddy.exe
    pause
    exit /b 1
)

echo [*] Configuring C:\caddy\Caddyfile...
(
    echo !DOMAIN! {
    echo     reverse_proxy 127.0.0.1:8000
    echo }
) > "C:\caddy\Caddyfile"

echo [*] Opening Windows Firewall for HTTP (80) and HTTPS (443)...
netsh advfirewall firewall add rule name="CMLS SSL HTTP 80" dir=in action=allow protocol=TCP localport=80 >nul 2>&1
netsh advfirewall firewall add rule name="CMLS SSL HTTPS 443" dir=in action=allow protocol=TCP localport=443 >nul 2>&1

echo [*] Registering 24x7 Caddy SSL Service in Task Scheduler...
schtasks /create /tn "ILoveFiles_SSL_Caddy" /tr "\"C:\caddy\caddy.exe\" run --config \"C:\caddy\Caddyfile\"" /sc onstart /ru SYSTEM /f >nul 2>&1

echo [*] Starting Caddy HTTPS Engine now...
cd /d C:\caddy
start "Caddy SSL" "C:\caddy\caddy.exe" run --config Caddyfile

echo.
echo ==========================================================
echo   [SUCCESS] Automatic Free SSL Configured!
echo =========================================================
echo.
echo Your app is now being secured with HTTPS:
echo https://!DOMAIN!
echo.
echo CRITICAL AZURE STEP:
echo 1. Open Azure Portal -^> Go to your Virtual Machine
echo 2. Click 'Networking' (or 'Network settings') on the left
echo 3. Click 'Add inbound port rule'
echo 4. Add Port 443 (Service: HTTPS, Action: Allow)
echo.
echo Press any key to exit...
pause >nul
exit /b 0

:norm_domain
set "DOMAIN=!DOMAIN: =!"
set "DOMAIN=!DOMAIN:http://=!"
set "DOMAIN=!DOMAIN:https://=!"
set "DOMAIN=!DOMAIN:/=!"

echo !DOMAIN!| findstr /r "^[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*$" >nul
if !errorlevel! equ 0 (
    echo.
    echo ==========================================================
    echo   [ERROR] You entered an IP address: !DOMAIN!
    echo ==========================================================
    echo Let's Encrypt CANNOT issue SSL certificates to an IP address!
    echo You must enter your Azure DNS domain name.
    echo.
    echo Example: ilovefiles.centralindia.cloudapp.azure.com
    echo.
    echo HOW TO FIND IT:
    echo 1. Azure Portal -^> Virtual Machines -^> Your VM
    echo 2. Click your Public IP address
    echo 3. Click 'Configuration' on the left
    echo 4. Type a name in 'DNS name label' and click Save.
    echo.
    pause
    exit /b 1
)
exit /b