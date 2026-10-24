@echo off
setlocal EnableDelayedExpansion
title RESONANCE CLUB - FASTAPI + SQLADMIN BACKEND

echo ====================================================================
echo   RESONANCE CLUB - FASTAPI + SQLADMIN AUTO CRUD BACKEND (v1.0.2)
echo ====================================================================
echo.

:: 1. Detect Python interpreter (python or py -3 or py)
set "PYCMD="

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
    if %ERRORLEVEL% equ 0 set "PYCMD=python"
)

if not defined PYCMD (
    where py >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
        if %ERRORLEVEL% equ 0 set "PYCMD=py -3"
    )
)

if not defined PYCMD (
    echo [ERROR] Python 3.8+ was not found in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check the box "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [INFO] Using Python interpreter: %PYCMD%
echo.

:: 2. Check and install dependencies via "python -m pip" (not raw "pip")
echo [1/3] Checking dependencies (fastapi, sqladmin, sqlalchemy, uvicorn)...
%PYCMD% -c "import fastapi, sqladmin, sqlalchemy, uvicorn, greenlet, aiosqlite, wtforms" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Required packages not found. Checking pip module...
    %PYCMD% -m pip --version >nul 2>&1
    if !ERRORLEVEL! neq 0 (
        echo [INFO] Bootstrapping pip via ensurepip...
        %PYCMD% -m ensurepip --default-pip >nul 2>&1
    )
    echo [INFO] Installing required packages via "%PYCMD% -m pip"...
    %PYCMD% -m pip install fastapi sqladmin sqlalchemy uvicorn aiosqlite greenlet wtforms
    if !ERRORLEVEL! neq 0 (
        echo [INFO] Trying user installation mode (--user)...
        %PYCMD% -m pip install --user fastapi sqladmin sqlalchemy uvicorn aiosqlite greenlet wtforms
    )
    %PYCMD% -c "import fastapi, sqladmin, sqlalchemy, uvicorn, greenlet, aiosqlite, wtforms" >nul 2>&1
    if !ERRORLEVEL! neq 0 (
        echo.
        echo [ERROR] Could not install required dependencies!
        echo Please ensure you have internet access and run manually:
        echo   %PYCMD% -m pip install fastapi sqladmin sqlalchemy uvicorn aiosqlite greenlet wtforms
        echo.
        pause
        exit /b 1
    )
)
echo [OK] All Python dependencies are verified.
echo.

:: 3. Initialize SQLite Database and 100 Questions Pool (using "and", NOT "&")
echo [2/3] Initializing Resonance Club Database and 100 Questions Pool...
%PYCMD% -c "from seed_db import seed_database; seed_database()"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Database initialization failed!
    pause
    exit /b 1
)
echo [OK] Database initialized successfully.
echo.

:: 4. Start Server and Open SQLAdmin in Default Browser
echo [3/3] Starting FastAPI + SQLAdmin server on http://localhost:3000/admin ...
start "" "http://localhost:3000/admin"

%PYCMD% app_admin.py --host 0.0.0.0 --port 3000

echo.
echo Server has stopped.
pause
