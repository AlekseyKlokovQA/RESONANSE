#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Остановка временного тестового сервера..."
if command -v docker &> /dev/null; then
    cd temp_server && docker compose down 2>/dev/null || true
fi
pkill -f "serve_limited.py" 2>/dev/null || true
echo "Тестовый сервер полностью остановлен. Все ресурсы освобождены."
