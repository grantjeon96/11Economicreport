@echo off
chcp 65001 > nul
set WORKSPACE_DIR=%~dp0
set BAT_PATH=%WORKSPACE_DIR%run_daily.bat

echo ===================================================
echo   [Register Daily Economic Indicator Scheduler]
echo ===================================================
echo.
echo This script will register run_daily.bat to Windows Task Scheduler.
echo.

REM Ask for Time (Default to 05:00)
set /p TARGET_TIME="Enter execution time (e.g. 05:00, default is 05:00): "
if "%TARGET_TIME%"=="" set TARGET_TIME=05:00

echo.
echo [Setup Info]
echo - Task Name: Economic_Daily_Report
echo - Action: %BAT_PATH%
echo - Run Time: %TARGET_TIME%
echo.
echo Registering task...
echo.

REM Run schtasks command to create task
schtasks /create /tn "Economic_Daily_Report" /tr "\"%BAT_PATH%\"" /sc daily /st %TARGET_TIME% /f

if %errorlevel% equ 0 (
    echo.
    echo ===================================================
    echo [SUCCESS] Windows Task successfully registered!
    echo Daily report will run at %TARGET_TIME% every morning.
    echo ===================================================
) else (
    echo.
    echo ===================================================
    echo [FAIL] Failed to register Windows Task.
    echo Please run this batch script as Administrator.
    echo ===================================================
)
echo.
pause
