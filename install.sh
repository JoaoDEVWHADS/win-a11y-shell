#!/usr/bin/env bash
# ==============================================================================
# win-a11y-shell Automated Installer for Ubuntu MATE (Win11 Theme) + Orca
# ==============================================================================

set -e

echo "=================================================="
echo "  Installing win-a11y-shell (Ubuntu MATE + Win11 GTK + Orca)"
echo "=================================================="

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root (sudo ./install.sh)"
  exit 1
fi

echo "[1/5] Installing MATE Desktop & Accessibility Packages..."
apt-get update -qq
apt-get install -y -qq \
    mate-desktop-environment-core \
    mate-panel \
    mate-applets \
    mate-menu \
    mate-media \
    marco \
    orca \
    speech-dispatcher \
    espeak-ng \
    alsa-utils \
    lightdm \
    lightdm-gtk-greeter \
    xdotool \
    wmctrl \
    gtk2-engines-murrine \
    gtk2-engines-pixbuf

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPT_DIR="/opt/win-a11y-shell"
mkdir -p "$OPT_DIR"

echo "[2/5] Installing Fluent Windows 11 GTK Theme..."
if [ -d "$SCRIPT_DIR/src/themes/Fluent-gtk-theme" ]; then
    cd "$SCRIPT_DIR/src/themes/Fluent-gtk-theme"
    chmod +x install.sh
    ./install.sh -c dark -t default --tweaks round || true
fi

# Definir tema do Windows 11 globalmente para GTK3 e MATE
mkdir -p /etc/skel/.config/gtk-3.0 /root/.config/gtk-3.0
cat << 'GTKCFG' > /etc/skel/.config/gtk-3.0/settings.ini
[Settings]
gtk-theme-name = Fluent-Dark
gtk-icon-theme-name = Fluent
gtk-font-name = Sans 10
gtk-cursor-theme-name = Yaru
GTKCFG
cp /etc/skel/.config/gtk-3.0/settings.ini /root/.config/gtk-3.0/settings.ini

echo "[3/5] Preserving & Syncing Orca Customized Engine..."
if [ -d "$SCRIPT_DIR/orca" ]; then
    cp -r "$SCRIPT_DIR/orca" "$OPT_DIR/"
fi

echo "[4/5] Installing Greeter & Launcher Scripts..."
cp "$SCRIPT_DIR/win-a11y-greeter-setup" /usr/local/bin/win-a11y-greeter-setup
chmod +x /usr/local/bin/win-a11y-greeter-setup
cp "$SCRIPT_DIR/win-a11y-shell" /usr/local/bin/win-a11y-shell
chmod +x /usr/local/bin/win-a11y-shell
cp "$SCRIPT_DIR/restart.sh" /usr/local/bin/win-a11y-restart
chmod +x /usr/local/bin/win-a11y-restart

echo "[5/5] Configuring Systemd Service & LightDM MATE Session..."
cat << 'SESS' > /usr/share/xsessions/win-a11y-shell.desktop
[Desktop Entry]
Name=win-a11y-shell (MATE Win11)
Comment=Ubuntu MATE Desktop with Windows 11 Theme and Orca
Exec=/usr/local/bin/win-a11y-shell
Type=Application
SESS

cp "$SCRIPT_DIR/win-a11y-shell.service" /etc/systemd/system/win-a11y-shell.service
systemctl daemon-reload
systemctl enable win-a11y-shell.service

echo "✅ Installation Complete! Run 'bash deploy.sh' or 'bash restart.sh' to launch."
