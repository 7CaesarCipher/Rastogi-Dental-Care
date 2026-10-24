@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if not exist ".venv\Scripts\python.exe" (
    echo Could not create the Python environment. Please install Python 3.11 or newer.
    pause
    exit /b 1
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    pause
    exit /b 1
)
echo Open http://127.0.0.1:8087 in your browser
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8087
pause
