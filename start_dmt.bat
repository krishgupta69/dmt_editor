@echo off
rem Launch DMT Video Editor using the Python 3.8 virtual environment

if not exist venv38\Scripts\python.exe (
    echo [ERROR] Virtual environment venv38 not found or corrupted.
    pause
    exit /b 1
)

echo [DMT] Starting Video Editor...
venv38\Scripts\python.exe src\main.py
