@echo off
setlocal
cd /d "%~dp0"
if exist "dist\SetelahJamMalam.exe" (
    start "" "dist\SetelahJamMalam.exe"
    exit /b 0
)
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -c "import pygame" >nul 2>nul
if errorlevel 1 (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" main.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo Game belum dapat dijalankan. Periksa pesan di atas dan README.md.
pause
exit /b 1
