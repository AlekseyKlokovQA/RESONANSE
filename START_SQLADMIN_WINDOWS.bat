@echo off
setlocal
cd /d "%~dp0"
title RESONANCE CLUB - FASTAPI + SQLADMIN BACKEND

echo ====================================================================
echo   RESONANCE CLUB - FASTAPI + SQLADMIN AUTO CRUD BACKEND v1.0.2
echo ====================================================================
echo.

set "PYCMD="
set "PYDIR="

rem --------------------------------------------------------------------
rem Phase 1: Check Python in standard system PATH
rem --------------------------------------------------------------------
call :test_cmd "python"
if defined PYCMD goto :found_python

call :test_cmd "py -3"
if defined PYCMD goto :found_python

call :test_cmd "py"
if defined PYCMD goto :found_python

rem --------------------------------------------------------------------
rem Phase 2: Search Python in standard Windows installation folders
rem --------------------------------------------------------------------
echo [INFO] Searching for Python in standard installation directories...

for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if not defined PYCMD call :test_path "%%D\python.exe"
)
if defined PYCMD goto :found_python

for /d %%D in ("C:\Program Files\Python3*") do (
    if not defined PYCMD call :test_path "%%D\python.exe"
)
if defined PYCMD goto :found_python

for /d %%D in ("C:\Python3*") do (
    if not defined PYCMD call :test_path "%%D\python.exe"
)
if defined PYCMD goto :found_python

for /d %%D in ("%USERPROFILE%\AppData\Local\Programs\Python\Python3*") do (
    if not defined PYCMD call :test_path "%%D\python.exe"
)
if defined PYCMD goto :found_python

for /d %%D in ("%USERPROFILE%\miniconda3" "%USERPROFILE%\anaconda3" "C:\miniconda3" "C:\anaconda3") do (
    if not defined PYCMD call :test_path "%%D\python.exe"
)
if defined PYCMD goto :found_python

rem Specific common version paths
if not defined PYCMD call :test_path "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not defined PYCMD call :test_path "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PYCMD call :test_path "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not defined PYCMD call :test_path "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
if not defined PYCMD call :test_path "C:\Program Files\Python313\python.exe"
if not defined PYCMD call :test_path "C:\Program Files\Python312\python.exe"
if not defined PYCMD call :test_path "C:\Program Files\Python311\python.exe"
if not defined PYCMD call :test_path "C:\Program Files\Python310\python.exe"
if not defined PYCMD call :test_path "C:\Python313\python.exe"
if not defined PYCMD call :test_path "C:\Python312\python.exe"
if not defined PYCMD call :test_path "C:\Python311\python.exe"
if not defined PYCMD call :test_path "C:\Python310\python.exe"

if defined PYCMD goto :found_python

rem --------------------------------------------------------------------
rem Phase 3: Python not found - Offer winget or Zero-Install Admin
rem --------------------------------------------------------------------
echo.
echo ====================================================================
echo   [ATTENTION] Python 3.8+ was not found on your system.
echo ====================================================================
echo.
echo   To launch the FastAPI + SQLAdmin backend, Python 3.8+ is needed.
echo.

where winget >nul 2>&1
if %ERRORLEVEL% equ 0 goto :offer_winget
goto :show_manual_options

:offer_winget
echo   Windows Package Manager (winget) is available on your computer.
echo   We can automatically download and install Python 3.12 for you.
echo.
set "DO_WINGET="
set /p "DO_WINGET=Do you want to automatically install Python 3.12 now? (Y/N): "
if /i "%DO_WINGET%"=="Y" goto :run_winget
goto :show_manual_options

:run_winget
echo.
echo [INFO] Downloading and installing Python 3.12 via winget...
winget install --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
echo.
echo [INFO] Searching for the newly installed Python...
call :test_path "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if defined PYCMD goto :found_python

echo [INFO] Installation finished. Please close this window and run
echo START_SQLADMIN_WINDOWS.bat again to start the server.
echo.
pause
exit /b 0

:show_manual_options
echo.
echo --------------------------------------------------------------------
echo   OPTION 1: Open Standalone Admin Panel (Zero-Install, instant!)
echo --------------------------------------------------------------------
echo   Open the Resonance Concierge Panel directly in your browser
echo   without installing Python!
echo.
set "DO_SPA="
set /p "DO_SPA=Open Zero-Install Admin Panel in browser right now? (Y/N): "
if /i "%DO_SPA%"=="Y" (
    if exist "admin.htm" start "" "admin.htm"
    if not exist "admin.htm" start "" "index.html"
    exit /b 0
)

echo.
echo --------------------------------------------------------------------
echo   OPTION 2: Install Python manually for SQLAdmin Backend
echo --------------------------------------------------------------------
echo   1. Download: https://www.python.org/downloads/
echo   2. Run installer and CHECK: [x] "Add python.exe to PATH"
echo   3. Run START_SQLADMIN_WINDOWS.bat again.
echo.
goto :error_exit

rem --------------------------------------------------------------------
rem Phase 4: Python is Found - Configure PATH and Environment
rem --------------------------------------------------------------------
:found_python
if defined PYDIR (
    echo [INFO] Located Python at: %PYDIR%
    set "PATH=%PYDIR%;%PYDIR%Scripts;%PATH%"
)
echo [INFO] Using Python launcher: %PYCMD%
%PYCMD% --version
echo.

rem --------------------------------------------------------------------
rem Phase 5: Check and install dependencies
rem --------------------------------------------------------------------
echo [1/3] Checking dependencies: fastapi, sqladmin, sqlalchemy, uvicorn, jinja2...

%PYCMD% -c "import fastapi, sqladmin, sqlalchemy, uvicorn, greenlet, aiosqlite, wtforms, jinja2" >nul 2>&1
if %ERRORLEVEL% equ 0 goto :check_opt_deps

echo [INFO] Some packages are missing. Installing via %PYCMD% -m pip...
echo.

%PYCMD% -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 %PYCMD% -m ensurepip --default-pip

%PYCMD% -m pip install fastapi sqladmin sqlalchemy uvicorn aiosqlite greenlet wtforms jinja2 python-multipart numpy
if %ERRORLEVEL% equ 0 goto :deps_verify

echo [INFO] Retrying with --user flag...
%PYCMD% -m pip install --user fastapi sqladmin sqlalchemy uvicorn aiosqlite greenlet wtforms jinja2 python-multipart numpy

:deps_verify
%PYCMD% -c "import fastapi, sqladmin, sqlalchemy, uvicorn, greenlet, aiosqlite, wtforms, jinja2" >nul 2>&1
if %ERRORLEVEL% equ 0 goto :check_opt_deps

echo.
echo [ERROR] Failed to install core dependencies automatically.
echo Please verify your internet connection, or run manually:
echo   %PYCMD% -m pip install fastapi sqladmin sqlalchemy uvicorn aiosqlite greenlet wtforms jinja2 python-multipart numpy
echo.
goto :error_exit

:check_opt_deps
%PYCMD% -c "import numpy" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Installing optional numpy for audio FFT analysis...
    %PYCMD% -m pip install numpy >nul 2>&1
)
echo [OK] All required dependencies are verified.
echo.

rem --------------------------------------------------------------------
rem Phase 6: Initialize Database and Question Bank
rem --------------------------------------------------------------------
echo [2/3] Initializing Resonance Club Database and 100 Questions Pool...
%PYCMD% -c "from seed_db import seed_database; seed_database()"
if %ERRORLEVEL% neq 0 goto :seed_fail
echo [OK] Database is ready.
echo.

rem --------------------------------------------------------------------
rem Phase 7: Free Port 3000 and Launch FastAPI + SQLAdmin Server
rem --------------------------------------------------------------------
:start_app
rem Check if port 3000 is occupied by an old PowerShell server or background process
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    echo [INFO] Port 3000 is occupied by existing process (PID: %%a). Freeing port 3000...
    taskkill /F /PID %%a >nul 2>&1
)

echo [3/3] Starting FastAPI + SQLAdmin backend on http://localhost:3000/admin/ ...
echo Opening browser...
start "" "http://localhost:3000/admin/"

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
echo The script has finished. Window will stay open for review.
echo ====================================================================
pause
exit /b 1

:normal_exit
pause
exit /b 0

rem --------------------------------------------------------------------
rem Subroutines
rem --------------------------------------------------------------------
:test_cmd
set "TEST_NAME=%~1"
%TEST_NAME% -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if %ERRORLEVEL% equ 0 set "PYCMD=%TEST_NAME%"
exit /b 0

:test_path
set "FILE_PATH=%~1"
if exist "%FILE_PATH%" (
    "%FILE_PATH%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PYCMD="%FILE_PATH%""
        for %%I in ("%FILE_PATH%") do set "PYDIR=%%~dpI"
    )
)
exit /b 0
