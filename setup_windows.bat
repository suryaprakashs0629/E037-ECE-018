@echo off
setlocal
cd /d "%~dp0"
echo ==========================================================
echo  TEAM E037 - Campus Walkie-Talkie Allocation Engine
echo  Windows setup and database initialisation
echo ==========================================================

if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  py -3.12 -m venv .venv >nul 2>&1
  if errorlevel 1 py -3 -m venv .venv
  if errorlevel 1 goto :failed
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :failed

echo Installing Python dependencies...
python -m pip install --upgrade pip
if errorlevel 1 goto :failed
pip install -r requirements.txt
if errorlevel 1 goto :failed

if not exist ".env" (
  copy ".env.example" ".env" >nul
  python -c "from pathlib import Path; import secrets; p=Path('.env'); s=p.read_text(encoding='utf-8'); p.write_text(s.replace('replace-with-a-long-random-secret', secrets.token_hex(32)), encoding='utf-8')"
  echo Created .env with a fresh secret and the SQLite quick-preview database setting.
)

echo Initialising database and official channel/group masters...
python scripts\init_db.py
if errorlevel 1 goto :failed

echo.
echo Create the first administrator account:
python scripts\create_admin.py
if errorlevel 1 goto :failed

echo.
echo Setup complete. Run run_windows.bat to start the website.
pause
exit /b 0

:failed
echo.
echo Setup stopped because a command failed. Read the message above, fix it, and run this file again.
pause
exit /b 1
