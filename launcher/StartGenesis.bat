@echo off
cd /d "%~dp0.."
echo Genesis Launcher...
py -m pip install -q -r launcher\requirements.txt
start "" pyw -m launcher
