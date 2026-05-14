@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [DataGuru] Creating virtual environment...
    python -m venv .venv
)

echo [DataGuru] Installing/updating dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [DataGuru] Dependency installation failed.
    exit /b 1
)

echo [DataGuru] Starting Streamlit UI...
".venv\Scripts\python.exe" -m streamlit run app.py
