#!/usr/bin/env bash
# restart.sh — mata TUDO relacionado ao win-a11y-shell e inicia do zero
set -e

echo "[restart] Parando systemd service..."
systemctl stop win-a11y-shell 2>/dev/null || true

echo "[restart] Matando bash wrapper (exceto este processo)..."
pkill -9 -f "win-a11y-shell" --ignore-ancestors 2>/dev/null || \
    pgrep -f "win-a11y-shell" | grep -v "$$" | grep -v "$PPID" | xargs -r kill -9 2>/dev/null || true

echo "[restart] Matando daemon.py..."
pkill -9 -f "daemon.py" 2>/dev/null || true

echo "[restart] Limpando lock file..."
rm -f /tmp/win_a11y_shell.lock

echo "[restart] Aguardando processos morrerem..."
sleep 2

echo "[restart] Verificando se sobrou algum processo..."
if pgrep -f "daemon.py" > /dev/null; then
    echo "[restart] AVISO: ainda há processos, forçando kill..."
    kill -9 $(pgrep -f daemon.py) 2>/dev/null || true
    sleep 1
fi

echo "[restart] Iniciando daemon limpo..."
export DISPLAY=:0
export GTK_MODULES=gail:atk-bridge
export NO_AT_BRIDGE=0
export ACCESSIBILITY_ENABLED=1
export GNOME_ACCESSIBILITY=1
export LANG=pt_BR.UTF-8
export LC_ALL=pt_BR.UTF-8
export LANGUAGE=pt_BR:pt
export PYTHONPATH="/opt/win-a11y-shell/orca/src:$PYTHONPATH"

nohup python3 /opt/win-a11y-shell/daemon.py > /tmp/win_a11y_daemon.log 2>&1 &
DAEMON_PID=$!

sleep 2

if ps -p $DAEMON_PID > /dev/null 2>&1; then
    echo "[restart] ✅ Daemon rodando (PID $DAEMON_PID)"
else
    echo "[restart] ❌ Daemon falhou ao iniciar. Veja /tmp/win_a11y_daemon.log"
    tail -20 /tmp/win_a11y_daemon.log
    exit 1
fi
