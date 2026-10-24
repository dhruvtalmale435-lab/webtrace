@echo off
REM Run from the project root.
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python -m uvicorn backend.main:app --port 8000
