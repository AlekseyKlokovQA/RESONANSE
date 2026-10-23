#!/usr/bin/env bash
# ==============================================================================
# Automated setup script for Resonance Club Platform on a Virtual Machine
# Supported OS: Ubuntu 20.04/22.04/24.04, Debian 11/12, AlmaLinux, Fedora, CentOS
# ==============================================================================

set -e

echo "=== [1/4] Проверка окружения и установка Python ==="
if command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y python3 ufw curl
elif command -v dnf &> /dev/null; then
    sudo dnf install -y python3 firewalld curl
elif command -v yum &> /dev/null; then
    sudo yum install -y python3 curl
fi

echo "=== [2/4] Настройка фаервола (порт 3000) ==="
if command -v ufw &> /dev/null; then
    sudo ufw allow 3000/tcp || true
elif command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --add-port=3000/tcp --permanent || true
    sudo firewall-cmd --reload || true
fi

echo "=== [3/4] Определение IP-адреса виртуальной машины ==="
VM_IP=$(hostname -I | awk '{print $1}')
echo "IP виртуальной машины: $VM_IP"

echo "=== [4/4] Запуск сервера Резонанс на порту 3000 ==="
echo "Для доступа с вашего основного компьютера откройте в браузере:"
echo "👉 http://${VM_IP}:3000/"
echo "👉 http://${VM_IP}:3000/profile.html"
echo ""
echo "Сервер запускается..."
python3 serve.py 3000
