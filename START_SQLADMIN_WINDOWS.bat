@echo off
setlocal
chcp 65001 >nul 2>&1
title RESONANCE CLUB - FASTAPI + SQLADMIN BACKEND

echo ====================================================================
echo   RESONANCE CLUB - FASTAPI + SQLADMIN AUTO CRUD BACKEND (v1.0.2)
echo ====================================================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found in PATH!
    echo Please install Python 3.10+ to run the FastAPI / SQLAdmin backend.
    echo.
    pause
    exit /b 1
)

echo [1/3] Checking dependencies (fastapi, sqladmin, sqlalchemy, uvicorn)...
python -c "import fastapi, sqladmin, sqlalchemy, uvicorn, greenlet, aiosqlite, wtforms" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Installing required packages...
    pip install fastapi sqladmin sqlalchemy uvicorn aiosqlite greenlet wtforms
)

echo [2/3] Initializing Resonance Club Database & 100 Questions Pool...
python -c "from seed_db import seed_database; seed_database()"

echo [3/3] Starting server on http://localhost:3000/admin ...
start "" "http://localhost:3000/admin"

python app_admin.py --host 0.0.0.0 --port 3000

pause
