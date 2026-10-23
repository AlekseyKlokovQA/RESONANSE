@echo off
setlocal
cd /d "%~dp0"
title Resonance Club Server - Port 3000
cls

echo ===================================================================
echo   RESONANCE CLUB - TEMPORARY TESTING SERVER (ZERO-INSTALL)
echo ===================================================================
echo.
echo [1/1] Launching native Windows server engine...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Unblock-File -LiteralPath '%~dp0server_windows_native.ps1' -ErrorAction SilentlyContinue; & '%~dp0server_windows_native.ps1' -Port 3000"

echo.
echo ===================================================================
echo Server has been stopped.
echo ===================================================================
pause
