#!/usr/bin/env bash
# ==============================================================================
# win-a11y-shell Installer (Debian Minimal Xorg + Openbox + Accessibility Shell)
# ==============================================================================

set -e

echo "=================================================="
echo "  Installing win-a11y-shell (Debian Accessibility)"
echo "=================================================="

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root (sudo ./install.sh)"
  exit 1
fi

echo "[1/6] Updating package lists..."
apt-get update -qq

echo "[2/6] Installing Xorg minimal display server & Openbox..."
apt-get install -y -qq \
    xserver-xorg-core \
    xinit \
    openbox \
    x11-xserver-utils \
    x11-utils \
    xdotool \
    nodm

echo "[3/6] Installing GTK3 & Speech Dispatcher dependencies..."
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-gi \
    gir1.2-gtk-3.0 \
    speech-dispatcher \
    python3-speechd \
    espeak-ng \
    python3-evdev

echo "[4/6] Installing application files to /opt/win-a11y-shell..."
mkdir -p /opt/win-a11y-shell
cp -rf src/* /opt/win-a11y-shell/

# Create launcher
cat << 'EOF' > /usr/local/bin/win-a11y-shell
#!/usr/bin/env bash
export DISPLAY=:0
python3 /opt/win-a11y-shell/daemon.py "$@"
EOF
chmod +x /usr/local/bin/win-a11y-shell

echo "[5/6] Configuring X11 autostart (~/.xinitrc)..."
cat << 'EOF' > /root/.xinitrc
#!/usr/bin/env bash
openbox &
python3 /opt/win-a11y-shell/daemon.py
EOF
chmod +x /root/.xinitrc

echo "[6/6] Configuring nodm auto-login for display server..."
cat << 'EOF' > /etc/default/nodm
NODM_ENABLED=true
NODM_USER=root
NODM_XSESSION=/root/.xinitrc
NODM_XUNSESSION=/etc/X11/Xsession
NODM_XSESSION_OLD=/root/.xinitrc
NODM_PATH=/usr/bin:/bin
NODM_MIN_SESSION_TIME=60
EOF

systemctl restart nodm || true

echo "=================================================="
echo "  INSTALLATION & XORG AUTO-LOGIN COMPLETE!"
echo "  The display server is now active on screen."
echo "=================================================="
