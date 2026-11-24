@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
python scripts\run_official.py
if errorlevel 1 pause
