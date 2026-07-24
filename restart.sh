#!/usr/bin/env bash
# restart.sh — reinicia daemon + Orca
#   Uso:
#     bash restart.sh           → reinicia só daemon e Orca (sessão atual)
#     bash restart.sh --greeter → mata TUDO e reinicia lightdm (nova tela de login com Orca)
set -e

# ─── Modo --greeter: mata tudo e reinicia lightdm ────────────────────────────
if [ "${1:-}" = "--greeter" ]; then
    echo "[restart] Modo GREETER — matando tudo e reiniciando lightdm..."
    pkill -9 -f "orca.orca"    2>/dev/null || true
    pkill -9 -f "daemon.py"    2>/dev/null || true
    pkill -9 -f "openbox"      2>/dev/null || true
    pkill -9 -f "win-a11y"     2>/dev/null || true
    pkill -9 -f "lightdm-gtk"  2>/dev/null || true
    rm -f /tmp/win_a11y_shell.lock
    sleep 2
    echo "[restart] Reiniciando lightdm (Orca será iniciado no greeter-setup-script)..."
    systemctl restart lightdm
    echo "[restart] ✅ lightdm reiniciado — tela de login com Orca ativa"
    exit 0
fi

# ─── Detectar DISPLAY e XAUTHORITY automaticamente ───────────────────────────
# Prioridade: sessão atual → lightdm root → fallback :0
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
fi

if [ -z "$XAUTHORITY" ]; then
    LDM_AUTH="/var/run/lightdm/root/${DISPLAY}"
    if [ -f "$LDM_AUTH" ]; then
        export XAUTHORITY="$LDM_AUTH"
    fi
fi

# Verificar se há display X11 disponível
if ! XAUTHORITY="${XAUTHORITY}" xdpyinfo -display "${DISPLAY}" > /dev/null 2>&1; then
    echo "[restart] ❌ Nenhum display X11 disponível em ${DISPLAY}."
    echo "[restart]    Execute dentro de uma sessão gráfica ativa."
    exit 1
fi

echo "[restart] ✅ Display: ${DISPLAY} | XAUTHORITY: ${XAUTHORITY:-não definido}"

# Variáveis de ambiente compartilhadas
ENV_VARS=(
    "DISPLAY=${DISPLAY}"
    "XAUTHORITY=${XAUTHORITY:-/var/run/lightdm/root/${DISPLAY}}"
    "GTK_MODULES=gail:atk-bridge"
    "NO_AT_BRIDGE=0"
    "ACCESSIBILITY_ENABLED=1"
    "GNOME_ACCESSIBILITY=1"
    "LANG=pt_BR.UTF-8"
    "LC_ALL=pt_BR.UTF-8"
    "LANGUAGE=pt_BR:pt"
    "PYTHONPATH=/opt/win-a11y-shell/orca/src:${PYTHONPATH}"
)

# ─── Parar serviços e processos ──────────────────────────────────────────────
echo "[restart] Parando systemd service..."
systemctl stop win-a11y-shell 2>/dev/null || true

echo "[restart] Matando daemon.py..."
pkill -9 -f "python3 /opt/win-a11y-shell/daemon.py" 2>/dev/null || true

echo "[restart] Matando Orca..."
pkill -9 -f "orca.orca" 2>/dev/null || true

echo "[restart] Limpando lock file..."
rm -f /tmp/win_a11y_shell.lock

echo "[restart] Aguardando processos morrerem..."
sleep 2

# Verificação extra
pgrep -f "daemon.py" | xargs -r kill -9 2>/dev/null || true
pgrep -f "orca.orca"  | xargs -r kill -9 2>/dev/null || true

# ─── Iniciar Orca ─────────────────────────────────────────────────────────────
echo "[restart] Iniciando Orca..."
nohup env "${ENV_VARS[@]}" /usr/local/bin/orca --replace > /tmp/win_a11y_orca.log 2>&1 &
ORCA_PID=$!
sleep 2

if ps -p $ORCA_PID > /dev/null 2>&1; then
    echo "[restart] ✅ Orca rodando (PID $ORCA_PID)"
else
    echo "[restart] ⚠️  Orca pode estar inicializando em background (verifique /tmp/win_a11y_orca.log)"
fi

# ─── Iniciar daemon ──────────────────────────────────────────────────────────
echo "[restart] Iniciando daemon win-a11y-shell..."
nohup env "${ENV_VARS[@]}" \
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

echo "[restart] ✅ Tudo rodando! Orca PID=$ORCA_PID | Daemon PID=$DAEMON_PID"
