@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Complete the Windows setup in README.md first.
    echo python -m venv .venv
    echo .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)
".venv\Scripts\python.exe" run.py
if errorlevel 1 pause
