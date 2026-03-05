@echo off
REM Battery Neural Core - Windows Launcher
REM Starts background service and opens dashboard

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Battery Neural Core - Windows Edition
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found
    echo Install from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Start background service
echo Starting background battery service...
start "Battery Service" cmd /k "cd /d "%cd%" && python src\backend\battery_service.py"
timeout /t 2 >nul

REM Start web server
echo Starting web server...
start "Battery Dashboard" cmd /k "cd /d "%cd%" && python src\backend\server.py 3000"
timeout /t 2 >nul

REM Open browser
echo Opening dashboard...
start "" "http://localhost:3000"

echo.
echo ========================================
echo   ✅ Dashboard is running!
echo ========================================
echo.
echo 📍 Dashboard: http://localhost:3000
echo 📊 Battery data folder: data\
echo.
echo Close these windows to stop.
echo.
pause
