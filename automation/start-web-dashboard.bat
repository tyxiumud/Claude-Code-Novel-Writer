@echo off
cd /d "%~dp0.."
echo Starting Web Dashboard...
echo.
python automation\web_dashboard.py --port 8080
pause
