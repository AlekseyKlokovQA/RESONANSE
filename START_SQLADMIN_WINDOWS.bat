@echo off
setlocal
cd /d "%~dp0"
title RESONANCE CLUB - FASTAPI + SQLADMIN BACKEND

echo ====================================================================
echo   RESONANCE CLUB - FASTAPI + SQLADMIN AUTO CRUD BACKEND v1.0.2
echo ====================================================================
echo.

rem Step 1: Detect working Python interpreter
set "PYCMD="

python -c "import sys" >nul 2>&1
if %ERRORLEVEL% equ 0 set "PYCMD=python"
if defined PYCMD goto :found_python

py -3 -c "import sys" >nul 2>&1
if %ERRORLEVEL% equ 0 set "PYCMD=py -3"
if defined PYCMD goto :found_python

py -c "import sys" >nul 2>&1
if %ERRORLEVEL% equ 0 set "PYCMD=py"
if defined PYCMD goto :found_python

echo [ERROR] Python was not found in your system PATH.
echo.
echo Please install Python 3.10+ from https://www.python.org/
echo IMPORTANT: During installation, make sure to check:
echo   [x] Add python.exe to PATH
echo.
goto :error_exit

:found_python
echo [INFO] Detected Python launcher: %PYCMD%
%PYCMD% --version
echo.

rem Step 2: Check required Python packages
echo [1/3] Checking dependencies: fastapi, sqladmin, sqlalchemy, uvicorn...

%PYCMD% -c "import fastapi, sqladmin, sqlalchemy, uvicorn, greenlet, aiosqlite, wtforms" >nul 2>&1
if %ERRORLEVEL% equ 0 goto :deps_ok

echo [INFO] Some packages are missing. Installing via %PYCMD% -m pip...
echo.

rem Ensure pip module is available
%PYCMD% -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 %PYCMD% -m ensurepip --default-pip

rem Install packages via pip
%PYCMD% -m pip install fastapi sqladmin sqlalchemy uvicorn aiosqlite greenlet wtforms
if %ERRORLEVEL% equ 0 goto :deps_verify

echo [INFO] Retrying installation with --user flag...
%PYCMD% -m pip install --user fastapi sqladmin sqlalchemy uvicorn aiosqlite greenlet wtforms

:deps_verify
%PYCMD% -c "import fastapi, sqladmin, sqlalchemy, uvicorn, greenlet, aiosqlite, wtforms" >nul 2>&1
if %ERRORLEVEL% equ 0 goto :deps_ok

echo.
echo [ERROR] Failed to install dependencies automatically.
echo Please verify your internet connection, or run manually in terminal:
echo   %PYCMD% -m pip install fastapi sqladmin sqlalchemy uvicorn aiosqlite greenlet wtforms
echo.
goto :error_exit

:deps_ok
echo [OK] All required dependencies are verified.
echo.

rem Step 3: Initialize Database and Question Bank
echo [2/3] Initializing Resonance Club Database and 100 Questions Pool...
%PYCMD% -c "from seed_db import seed_database; seed_database()"
if %ERRORLEVEL% neq 0 goto :seed_fail
echo [OK] Database is ready.
echo.
goto :start_app

:seed_fail
echo.
echo [ERROR] Database initialization failed.
echo.
goto :error_exit

:start_app
rem Step 4: Launch FastAPI + SQLAdmin Server
echo [3/3] Starting FastAPI + SQLAdmin backend on http://localhost:3000/admin ...
echo Opening browser...
start "" "http://localhost:3000/admin"

%PYCMD% app_admin.py --host 0.0.0.0 --port 3000
if %ERRORLEVEL% neq 0 goto :app_fail

echo.
echo Server stopped normally.
goto :normal_exit

:app_fail
echo.
echo [ERROR] Server exited with code %ERRORLEVEL%.
goto :error_exit

:error_exit
echo.
echo ====================================================================
echo An error occurred. The window will stay open so you can read it.
echo ====================================================================
pause
exit /b 1

:normal_exit
pause
exit /b 0
