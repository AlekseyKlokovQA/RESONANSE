#!/usr/bin/env bash
# ====================================================================
# Resonance Club — FastAPI + SQLAdmin Launcher for Linux / macOS
# ====================================================================

set -e

PORT=${1:-3000}
HOST="0.0.0.0"

echo "===================================================================="
echo "  RESONANCE CLUB — FASTAPI + SQLADMIN AUTO CRUD BACKEND (v1.0.2)"
echo "===================================================================="
echo ""

echo "Checking Python 3 environment..."
python3 -c "import fastapi, sqladmin, sqlalchemy, uvicorn, greenlet, aiosqlite, wtforms" 2>/dev/null || {
    echo "Installing missing dependencies..."
    pip install fastapi sqladmin sqlalchemy uvicorn aiosqlite greenlet wtforms
}

echo "Initializing database..."
python3 -c "from seed_db import seed_database; seed_database()"

echo "Starting server on http://${HOST}:${PORT}/admin ..."
python3 app_admin.py --host "${HOST}" --port "${PORT}"
