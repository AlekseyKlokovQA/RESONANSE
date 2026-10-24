# Resonance Club — FastAPI + SQLAdmin Launcher (PowerShell)
Set-Location $PSScriptRoot

Write-Host "====================================================================" -ForegroundColor Yellow
Write-Host "  RESONANCE CLUB — FASTAPI + SQLADMIN AUTO CRUD BACKEND v1.0.2" -ForegroundColor Yellow
Write-Host "====================================================================" -ForegroundColor Yellow
Write-Host ""

# 1. Search Python in PATH
$pyExe = $null
$pyPrefix = @()

if (Get-Command "python" -ErrorAction SilentlyContinue) {
    & python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $pyExe = "python"
        $pyPrefix = @()
    }
}

if (-not $pyExe -and (Get-Command "py" -ErrorAction SilentlyContinue)) {
    & py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $pyExe = "py"
        $pyPrefix = @("-3")
    }
}

# 2. Search Python in standard installation folders
if (-not $pyExe) {
    Write-Host "[INFO] Searching standard Windows installation folders..." -ForegroundColor Cyan
    $searchPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe",
        "C:\Program Files\Python3*\python.exe",
        "C:\Python3*\python.exe",
        "$env:USERPROFILE\miniconda3\python.exe",
        "$env:USERPROFILE\anaconda3\python.exe"
    )

    foreach ($pattern in $searchPaths) {
        $found = Get-Item $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            & $found.FullName -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $pyExe = $found.FullName
                $pyPrefix = @()
                $dir = $found.DirectoryName
                $env:PATH = "$dir;$dir\Scripts;$env:PATH"
                Write-Host "[INFO] Located Python at: $dir" -ForegroundColor Green
                break
            }
        }
    }
}

# 3. If still not found, offer winget or admin.htm
if (-not $pyExe) {
    Write-Host "[ATTENTION] Python 3.8+ was not found on your PC." -ForegroundColor Red
    Write-Host ""

    if (Get-Command "winget" -ErrorAction SilentlyContinue) {
        $ans = Read-Host "Windows Package Manager (winget) is available. Install Python 3.12 automatically? (Y/N)"
        if ($ans -eq "Y" -or $ans -eq "y") {
            Write-Host "[INFO] Installing Python 3.12 via winget..." -ForegroundColor Cyan
            winget install --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
            Write-Host "Please restart this script after installation completes." -ForegroundColor Yellow
            Read-Host "Press Enter to exit..."
            exit 0
        }
    }

    $spa = Read-Host "Open Zero-Install Admin Panel (admin.htm) directly in browser? (Y/N)"
    if ($spa -eq "Y" -or $spa -eq "y") {
        if (Test-Path "admin.htm") { Start-Process "admin.htm" }
        else { Start-Process "index.html" }
        exit 0
    }

    Write-Host "Please install Python from https://www.python.org/ (check 'Add to PATH')."
    Read-Host "Press Enter to exit..."
    exit 1
}

Write-Host "[INFO] Using Python: $pyExe" -ForegroundColor Cyan
& $pyExe $pyPrefix --version
Write-Host ""

# 4. Check dependencies
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

# 5. Initialize Database
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

# 6. Start Server
Write-Host "[3/3] Starting FastAPI + SQLAdmin backend on http://localhost:3000/admin ..." -ForegroundColor Yellow
Start-Process "http://localhost:3000/admin"

& $pyExe $pyPrefix app_admin.py --host 0.0.0.0 --port 3000

Write-Host ""
Write-Host "Server stopped."
Read-Host "Press Enter to exit..."
