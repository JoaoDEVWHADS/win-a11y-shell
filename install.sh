#!/usr/bin/env bash
# ==============================================================================
# win-a11y-shell Automatic Installer for Debian-based systems
# High Accessibility Windows-like Desktop Shell for visually impaired users
# ==============================================================================

set -e

echo "=================================================="
echo "  Installing win-a11y-shell (Debian Accessibility)"
echo "=================================================="

# Check root privileges
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run the installer as root (sudo ./install.sh)"
  exit 1
fi

echo "[1/4] Updating package lists..."
apt-get update -qq

echo "[2/4] Installing system dependencies (Python3, PyGObject, AT-SPI2, Speech Dispatcher)..."
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    gir1.2-atspi-2.0 \
    speech-dispatcher \
    python3-speechd \
    orca \
    xbindkeys \
    x11-utils \
    xdotool

echo "[3/4] Installing Python application..."
mkdir -p /opt/win-a11y-shell
cp -r src/* /opt/win-a11y-shell/

# Create launcher binary
cat << 'EOF' > /usr/local/bin/win-a11y-shell
#!/usr/bin/env bash
python3 /opt/win-a11y-shell/main.py "$@"
EOF
chmod +x /usr/local/bin/win-a11y-shell

echo "[4/4] Installation complete!"
echo ""
echo "To start the shell, run: win-a11y-shell"
echo "=================================================="
