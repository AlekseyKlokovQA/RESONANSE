# Resonance Club — FastAPI + SQLAdmin Launcher (PowerShell)
Set-Location $PSScriptRoot

Write-Host "====================================================================" -ForegroundColor Yellow
Write-Host "  RESONANCE CLUB — FASTAPI + SQLADMIN AUTO CRUD BACKEND v1.0.2" -ForegroundColor Yellow
Write-Host "====================================================================" -ForegroundColor Yellow
Write-Host ""

# 1. Detect Python
$pyExe = $null
$pyPrefix = @()

if (Get-Command "python" -ErrorAction SilentlyContinue) {
    & python -c "import sys" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $pyExe = "python"
        $pyPrefix = @()
    }
}

if (-not $pyExe -and (Get-Command "py" -ErrorAction SilentlyContinue)) {
    & py -3 -c "import sys" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $pyExe = "py"
        $pyPrefix = @("-3")
    }
}

if (-not $pyExe) {
    Write-Host "[ERROR] Python 3.8+ was not found in PATH." -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/ (check 'Add to PATH')."
    Write-Host ""
    Read-Host "Press Enter to exit..."
    exit 1
}

Write-Host "[INFO] Detected Python executable: $pyExe" -ForegroundColor Cyan
& $pyExe $pyPrefix --version
Write-Host ""

# 2. Check dependencies
Write-Host "[1/3] Checking dependencies: fastapi, sqladmin, sqlalchemy, uvicorn..." -ForegroundColor Cyan
& $pyExe $pyPrefix -c "import fastapi, sqladmin, sqlalchemy, uvicorn, greenlet, aiosqlite, wtforms" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[INFO] Missing dependencies. Installing via pip..." -ForegroundColor Yellow
    & $pyExe $pyPrefix -m pip install fastapi sqladmin sqlalchemy uvicorn aiosqlite greenlet wtforms
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[INFO] Retrying with --user..." -ForegroundColor Yellow
        & $pyExe $pyPrefix -m pip install --user fastapi sqladmin sqlalchemy uvicorn aiosqlite greenlet wtforms
    }
}
Write-Host "[OK] Dependencies verified." -ForegroundColor Green
Write-Host ""

# 3. Initialize Database
Write-Host "[2/3] Initializing Resonance Club Database..." -ForegroundColor Cyan
& $pyExe $pyPrefix -c "from seed_db import seed_database; seed_database()"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Database initialization failed." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit..."
    exit 1
}
Write-Host "[OK] Database ready." -ForegroundColor Green
Write-Host ""

# 4. Start Server
Write-Host "[3/3] Starting FastAPI + SQLAdmin backend on http://localhost:3000/admin ..." -ForegroundColor Yellow
Start-Process "http://localhost:3000/admin"

& $pyExe $pyPrefix app_admin.py --host 0.0.0.0 --port 3000

Write-Host ""
Write-Host "Server stopped."
Read-Host "Press Enter to exit..."
