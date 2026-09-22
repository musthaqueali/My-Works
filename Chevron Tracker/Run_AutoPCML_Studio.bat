@echo off
title AutoPCML Studio - AutoCAD DWG to PCML Compiler
color 0B

echo ===============================================================================
echo     PINNACLE - AutoPCML Studio (AutoCAD DWG to CML Digital Twin)
echo ===============================================================================
echo.
echo [1/3] Detecting AutoCAD 2026 Engine...
if exist "C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe" (
    echo       [OK] Found AutoCAD 2026 Core Console: C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe
) else (
    echo       [WARNING] AutoCAD 2026 console not at default path. Proceeding with ezdxf mode...
)
echo.
echo [2/3] Processing AutoCAD DWG files from Desktop\DWGs...
python autopcml_dwg_compiler.py --dwgDir "C:\Users\musthaque.mayalankot\OneDrive - Pinnacle\Desktop\DWGs" --out "PCML_Database_Batch_All_DWGs.xlsx"

echo.
echo [3/3] Launching AutoPCML Studio Workstation...
start "" "autopcml_studio.html"

echo.
echo ===============================================================================
echo     AutoPCML Studio is now open in your browser!
echo     Generated Database: PCML_Database_Batch_All_DWGs.xlsx
echo ===============================================================================
echo.
pause
