#!/usr/bin/env bash
# ==============================================================================
# win-a11y-shell Automatic Installer & Systemd Auto-Start Configurator
# ==============================================================================

set -e

echo "=================================================="
echo "  Installing win-a11y-shell (Debian Accessibility)"
echo "=================================================="

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root (sudo ./install.sh)"
  exit 1
fi

echo "[1/5] Updating package lists..."
apt-get update -qq

echo "[2/5] Installing system packages & speech dependencies..."
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-gi \
    speech-dispatcher \
    python3-speechd \
    espeak-ng \
    xdotool \
    x11-utils

echo "[3/5] Installing Python keyboard hooks (pynput)..."
pip3 install --break-system-packages pynput || pip3 install pynput

echo "[4/5] Installing application files..."
mkdir -p /opt/win-a11y-shell
cp -r src/* /opt/win-a11y-shell/

# Create executable launcher
cat << 'EOF' > /usr/local/bin/win-a11y-shell
#!/usr/bin/env bash
python3 /opt/win-a11y-shell/daemon.py "$@"
EOF
chmod +x /usr/local/bin/win-a11y-shell

echo "[5/5] Configuring systemd Auto-Start on System Boot..."
cp win-a11y-shell.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable win-a11y-shell.service
systemctl restart win-a11y-shell.service || true

echo "=================================================="
echo "  INSTALLATION & AUTO-START COMPLETE!"
echo "  The system is now running in real-time."
echo "  Test keybindings anytime: Press Windows+B or Windows+M"
echo "=================================================="
