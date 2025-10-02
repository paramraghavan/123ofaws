@echo off
setlocal enabledelayedexpansion
cls

echo ======================================
echo   AWS Failover Manager Launcher
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt

REM Create directories
if not exist "logs\" mkdir logs
if not exist "templates\" mkdir templates

echo.
echo ======================================
echo   Choose an option:
echo ======================================
echo 1) Run failover detection ^& status logging
echo 2) Start Flask web dashboard
echo 3) Run failover with auto-restart (EC2 ^& EMR)
echo 4) Restart specific EMR cluster
echo 5) View recent logs
echo 6) Exit
echo.

set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto detection
if "%choice%"=="2" goto dashboard
if "%choice%"=="3" goto failover
if "%choice%"=="4" goto restart_emr
if "%choice%"=="5" goto viewlogs
if "%choice%"=="6" goto exit
goto invalid

:detection
echo.
echo Running failover detection...
python failover.py
goto end

:dashboard
echo.
echo Starting Flask web dashboard...
echo Access at: http://localhost:5000
echo Press Ctrl+C to stop
echo.
python app.py
goto end

:failover
echo.
echo WARNING: This will restart EC2 instances and recreate EMR clusters!
set /p confirm="Are you sure? (yes/no): "
if /i "%confirm%"=="yes" (
    echo Running failover with auto-restart...
    python failover.py
) else (
    echo Failover cancelled
)
goto end

:restart_emr
echo.
echo Restart specific EMR cluster
set /p cluster_id="Enter cluster ID (e.g., j-XXXXXXXXXXXXX): "
if not "%cluster_id%"=="" (
    echo WARNING: This will terminate and recreate cluster %cluster_id%
    set /p confirm="Are you sure? (yes/no): "
    if /i "!confirm!"=="yes" (
        python -c "from failover import AWSFailoverManager; m = AWSFailoverManager(); m.restart_emr_cluster('%cluster_id%')"
    ) else (
        echo Restart cancelled
    )
) else (
    echo No cluster ID provided
)
goto end

:viewlogs
echo.
echo Recent logs:
echo ======================================
if exist "logs\failover.log" (
    powershell -Command "Get-Content logs\failover.log -Tail 20"
) else (
    echo No logs found. Run detection first.
)
echo.
pause
goto end

:invalid
echo Invalid choice
pause
goto end

:exit
echo Goodbye!
goto end

:end
REM Deactivate virtual environment
call venv\Scripts\deactivate.bat