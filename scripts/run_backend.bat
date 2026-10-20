@echo off
REM Starts the SovereignAI backend (run from anywhere).
cd /d "%~dp0..\backend"
if not exist .venv (
  echo Creating virtual environment...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -r requirements.txt
if not exist .env copy .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
