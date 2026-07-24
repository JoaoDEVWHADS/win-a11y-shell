#!/usr/bin/env bash
# restart.sh — mata TUDO relacionado ao win-a11y-shell e inicia do zero
set -e

# Detectar DISPLAY e XAUTHORITY automaticamente
# Prioridade: sessão atual → lightdm root → fallback :0
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
fi

if [ -z "$XAUTHORITY" ]; then
    # Lightdm armazena o cookie em /var/run/lightdm/<user>/<display>
    LDM_AUTH="/var/run/lightdm/root/${DISPLAY}"
    if [ -f "$LDM_AUTH" ]; then
        export XAUTHORITY="$LDM_AUTH"
    fi
fi

# Verificar se há display X11 disponível
if ! XAUTHORITY="${XAUTHORITY}" xdpyinfo -display "${DISPLAY}" > /dev/null 2>&1; then
    echo "[restart] ❌ Nenhum display X11 disponível em ${DISPLAY}."
    echo "[restart]    Execute este script dentro de uma sessão gráfica ativa."
    echo "[restart]    (Ex: abra um terminal dentro do win-a11y-shell ou GNOME)"
    exit 1
fi

echo "[restart] ✅ Display: ${DISPLAY} | XAUTHORITY: ${XAUTHORITY:-não definido}"

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

# Detecta DISPLAY ativo — usa :0 como fallback
ACTIVE_DISPLAY="${DISPLAY:-:0}"

nohup env \
    DISPLAY="$ACTIVE_DISPLAY" \
    GTK_MODULES=gail:atk-bridge \
    NO_AT_BRIDGE=0 \
    ACCESSIBILITY_ENABLED=1 \
    GNOME_ACCESSIBILITY=1 \
    LANG=pt_BR.UTF-8 \
    LC_ALL=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt \
    PYTHONPATH="/opt/win-a11y-shell/orca/src:${PYTHONPATH}" \
    XAUTHORITY="${XAUTHORITY:-/var/run/lightdm/root/${DISPLAY}}" \
    python3 /opt/win-a11y-shell/daemon.py > /tmp/win_a11y_daemon.log 2>&1 &
DAEMON_PID=$!

sleep 3

if ps -p $DAEMON_PID > /dev/null 2>&1; then
    echo "[restart] ✅ Daemon rodando (PID $DAEMON_PID)"
else
    echo "[restart] ❌ Daemon falhou ao iniciar. Veja /tmp/win_a11y_daemon.log"
    tail -20 /tmp/win_a11y_daemon.log
    exit 1
fi
