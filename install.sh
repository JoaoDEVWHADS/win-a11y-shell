#!/usr/bin/env bash
# ==============================================================================
# win-a11y-shell Automated Installer for Windows 11 UI + Orca Integration
# ==============================================================================

set -e

echo "=================================================="
echo "  Installing win-a11y-shell (Windows 11 UI + Orca)"
echo "=================================================="

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root (sudo ./install.sh)"
  exit 1
fi

echo "[1/6] Installing Node.js, Google Chrome & System Packages..."
if ! command -v node >/dev/null 2>&1; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
fi

# Instalação automatizada do Google Chrome Oficial
if ! command -v google-chrome >/dev/null 2>&1 && ! command -v chromium >/dev/null 2>&1; then
    echo "[1/6] Instalando Google Chrome..."
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O /tmp/google-chrome.deb || true
    apt-get update -qq
    apt-get install -y /tmp/google-chrome.deb || apt-get install -y chromium
    rm -f /tmp/google-chrome.deb
fi

apt-get update -qq
apt-get install -y -qq \
    nodejs \
    chromium \
    orca \
    speech-dispatcher \
    espeak-ng \
    alsa-utils \
    xserver-xorg-core \
    xinit \
    openbox \
    lightdm \
    xdotool \
    wmctrl

echo "[2/6] Building Windows 11 UI Core..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIN11_SRC="$SCRIPT_DIR/src/win11"
OPT_DIR="/opt/win-a11y-shell"

mkdir -p "$OPT_DIR"

if [ -d "$WIN11_SRC" ]; then
    cd "$WIN11_SRC"
    npm install --legacy-peer-deps
    npm run build
    mkdir -p "$OPT_DIR/ui"
    rm -rf "$OPT_DIR/ui/*"
    if [ -d "$WIN11_SRC/build" ]; then
        cp -r "$WIN11_SRC/build/"* "$OPT_DIR/ui/"
    elif [ -d "$WIN11_SRC/dist" ]; then
        cp -r "$WIN11_SRC/dist/"* "$OPT_DIR/ui/"
    fi
fi

echo "[3/6] Preserving & Syncing Orca Customized Engine..."
if [ -d "$SCRIPT_DIR/orca" ]; then
    cp -r "$SCRIPT_DIR/orca" "$OPT_DIR/"
fi

echo "[4/6] Installing Greeter & Daemon Scripts..."
cp "$SCRIPT_DIR/win-a11y-greeter-setup" /usr/local/bin/win-a11y-greeter-setup
chmod +x /usr/local/bin/win-a11y-greeter-setup
cp "$SCRIPT_DIR/win-a11y-shell" /usr/local/bin/win-a11y-shell
chmod +x /usr/local/bin/win-a11y-shell
cp "$SCRIPT_DIR/restart.sh" /usr/local/bin/win-a11y-restart
chmod +x /usr/local/bin/win-a11y-restart

echo "[5/6] Configuring Systemd Service..."
cp "$SCRIPT_DIR/win-a11y-shell.service" /etc/systemd/system/win-a11y-shell.service
systemctl daemon-reload
systemctl enable win-a11y-shell.service

echo "[6/6] ✅ Installation Complete! Run 'bash deploy.sh' or 'bash restart.sh' to launch."
