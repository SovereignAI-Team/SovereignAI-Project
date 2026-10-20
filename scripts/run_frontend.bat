@echo off
REM Starts the SovereignAI frontend dev server on http://localhost:5173
cd /d "%~dp0..\frontend"
if not exist node_modules call npm install
call npm run dev
