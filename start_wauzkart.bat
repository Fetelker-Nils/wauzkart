@echo off
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
start "" pythonw launcher.py
