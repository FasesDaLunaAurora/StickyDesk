@echo off
REM Inicia o StickyDesk usando o Python do ambiente virtual, sem abrir console.
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "main.py"
) else (
    start "" pythonw "main.py"
)
