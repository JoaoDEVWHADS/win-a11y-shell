#!/usr/bin/env bash
# restart.sh — Reinicia o Orca personalizado e a nova interface gráfica do Windows 11
set -e

# Modo --greeter: reinicia lightdm
if [ "${1:-}" = "--greeter" ]; then
    echo "[restart] Modo GREETER — matando processos e reiniciando lightdm..."
    pkill -9 -f "orca"         2>/dev/null || true
    pkill -9 -f "chromium"     2>/dev/null || true
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

echo "[restart] Parando processos antigos..."
systemctl stop win-a11y-shell 2>/dev/null || true
pkill -9 -f "chromium" 2>/dev/null || true
pkill -9 -f "orca" 2>/dev/null || true
pkill -9 -f "http-server" 2>/dev/null || true
sleep 1

echo "[restart] Iniciando Orca personalizado..."
nohup env "${ENV_VARS[@]}" /usr/local/bin/orca --replace > /tmp/win_a11y_orca.log 2>&1 &
ORCA_PID=$!
sleep 2

echo "[restart] Servindo e abrindo a interface do Windows 11 em Kiosk Mode..."
if ! command -v npx >/dev/null 2>&1; then
    apt-get install -y nodejs npm 2>/dev/null || true
fi

# Servir static build em background
npx --yes http-server /opt/win-a11y-shell/ui -p 3000 --cors > /tmp/win_a11y_web.log 2>&1 &
sleep 2

# Abrir Chromium em tela cheia (Kiosk Mode) com flags de acessibilidade ativadas para o Orca
if command -v chromium >/dev/null 2>&1; then
    BROWSER_CMD="chromium"
elif command -v chromium-browser >/dev/null 2>&1; then
    BROWSER_CMD="chromium-browser"
else
    BROWSER_CMD="google-chrome"
fi

nohup env "${ENV_VARS[@]}" $BROWSER_CMD \
    --no-sandbox \
    --test-type \
    --kiosk \
    --force-renderer-accessibility \
    --enable-caret-browsing \
    --no-first-run \
    --disable-session-crashed-bubble \
    "http://localhost:3000" > /tmp/win_a11y_ui.log 2>&1 &

UI_PID=$!
echo "[restart] ✅ Orca PID=$ORCA_PID | Windows 11 UI PID=$UI_PID"
