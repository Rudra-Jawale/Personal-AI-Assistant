@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "AVA" ".venv\Scripts\pythonw.exe" start_ava.py
) else if exist ".venv\Scripts\python.exe" (
    start "AVA" ".venv\Scripts\python.exe" start_ava.py
) else (
    start "AVA" pythonw start_ava.py
)
