@echo off
REM =========================================================================
REM Battery Neural Core - Background Service Installer
REM Sets up the battery_service.py to run silently on Windows startup
REM =========================================================================

echo -----------------------------------------------------------------
echo Installing Battery Neural Core Background Service
echo -----------------------------------------------------------------
echo.

set "SCRIPT_DIR=%~dp0"
set "SERVICE_SCRIPT=%SCRIPT_DIR%battery_service.py"
set "VBS_SCRIPT=%SCRIPT_DIR%silent_runner.vbs"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\BatteryNeuralCore.lnk"

REM 1. Verify python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH!
    echo Please install Python and add it to your PATH before installing.
    pause
    exit /b 1
)

REM 2. Create the silent VBScript runner
echo [1/3] Creating invisible VBScript runner...
(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo WshShell.Run "python """ ^& "%SERVICE_SCRIPT%" ^& """", 0, False
) > "%VBS_SCRIPT%"

REM 3. Create the shortcut in the Startup folder using PowerShell
echo [2/3] Registering with Windows Startup...
powershell -Command "$wshell = New-Object -ComObject WScript.Shell; $shortcut = $wshell.CreateShortcut('%SHORTCUT_PATH%'); $shortcut.TargetPath = 'wscript.exe'; $shortcut.Arguments = '\"%VBS_SCRIPT%\"'; $shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $shortcut.Description = 'Battery Neural Core Telemetry'; $shortcut.Save()"

REM 4. Start the service immediately
echo [3/3] Starting the background service now...
wscript.exe "%VBS_SCRIPT%"

echo.
echo =================================================================
echo SUCCESS: The Background Service is now installed!
echo.
echo - The telemetry logger is currently running invisibly.
echo - It will automatically start every time you log into Windows.
echo - Logs are saved to: %SCRIPT_DIR%battery_history.csv
echo =================================================================
echo.
pause
