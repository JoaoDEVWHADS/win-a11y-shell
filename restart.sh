#!/usr/bin/env bash
# restart.sh — Reinicia MATE Desktop + Orca
set -e

if [ "${1:-}" = "--greeter" ]; then
    echo "[restart] Modo GREETER — matando processos e reiniciando lightdm..."
    pkill -9 -f "orca"         2>/dev/null || true
    pkill -9 -f "mate-session" 2>/dev/null || true
    pkill -9 -f "lightdm-gtk"  2>/dev/null || true
    sleep 2
    systemctl restart lightdm
    echo "[restart] ✅ lightdm reiniciado com Orca"
    exit 0
fi

if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
fi

if [ -z "$XAUTHORITY" ]; then
    LDM_AUTH="/var/run/lightdm/root/${DISPLAY}"
    if [ -f "$LDM_AUTH" ]; then
        export XAUTHORITY="$LDM_AUTH"
    fi
fi

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

echo "[restart] Parando Orca antigo..."
pkill -9 -f "orca" 2>/dev/null || true
sleep 1

echo "[restart] Iniciando Orca personalizado..."
nohup env "${ENV_VARS[@]}" /usr/local/bin/orca --replace > /tmp/win_a11y_orca.log 2>&1 &
ORCA_PID=$!
sleep 2

echo "[restart] Aplicando tema Fluent-Dark no GTK3..."
gsettings set org.mate.interface gtk-theme 'Fluent-Dark' 2>/dev/null || true
gsettings set org.gnome.desktop.interface gtk-theme 'Fluent-Dark' 2>/dev/null || true

echo "[restart] ✅ Orca PID=$ORCA_PID | Tema Windows 11 GTK3 Aplicado!"
