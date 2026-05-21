@echo off
set WORKSPACE_DIR=%~dp0
cd /d "%WORKSPACE_DIR%"

echo [1/3] Collecting economic metrics...
".\.venv2\Scripts\python.exe" "backend\collector.py"

echo [2/3] Generating and sending email report...
".\.venv2\Scripts\python.exe" "backend\notifier.py"

echo [3/3] Playing alarm and TTS briefing...
".\.venv2\Scripts\python.exe" "backend\alarm.py"

echo [SUCCESS] Script finished.
pause


