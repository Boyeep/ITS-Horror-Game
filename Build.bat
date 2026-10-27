@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" tools\build_release.py
if errorlevel 1 goto failed
echo.
echo Selesai: dist\SetelahJamMalam.exe dan ZIP portable.
exit /b 0
:failed
echo Build gagal. Periksa pesan di atas.
pause
exit /b 1
