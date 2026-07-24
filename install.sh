#!/usr/bin/env bash
# ==============================================================================
# win-a11y-shell Complete Automated Installer & Orca Integration
# ==============================================================================

set -e

echo "=================================================="
echo "  Installing win-a11y-shell (Complete Orca Debian)"
echo "=================================================="

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root (sudo ./install.sh)"
  exit 1
fi

echo "[1/7] Purging console audio locks (espeakup)..."
apt-get purge -y espeakup 2>/dev/null || true

echo "[2/7] Configuring ALSA Shared Audio (dmix)..."
cat << 'EOF' > /etc/asound.conf
pcm.!default {
    type plug
    slave.pcm "dmixer"
}
pcm.dmixer {
    type dmix
    ipc_key 1024
    ipc_key_add_uid false
    ipc_perm 0666
    slave {
        pcm "hw:0,0"
        period_time 0
        period_size 1024
        buffer_size 4096
        rate 44100
    }
    bindings {
        0 0
        1 1
    }
}
ctl.!default {
    type hw
    card 0
}
EOF

echo "[3/7] Updating package lists..."
apt-get update -qq

echo "[4/7] Installing Orca, GNOME Terminal, GTK3 & Accessibility Packages..."
apt-get install -y -qq \
    orca \
    gnome-terminal \
    python3-pyatspi \
    gir1.2-atspi-2.0 \
    dbus-x11 \
    libglib2.0-bin \
    speech-dispatcher \
    python3-speechd \
    espeak-ng \
    alsa-utils \
    xserver-xorg-core \
    xinit \
    openbox \
    x11-xserver-utils \
    x11-utils \
    xdotool \
    xdotool \
    wmctrl \
    nodm \
    python3 \
    python3-pip \
    python3-gi \
    gir1.2-gtk-3.0 \
    python3-evdev

cat << 'EOF' > /etc/environment
DISPLAY=:0
GTK_MODULES=gail:atk-bridge
QT_ACCESSIBILITY=1
NO_AT_BRIDGE=0
ACCESSIBILITY_ENABLED=1
GNOME_ACCESSIBILITY=1
EOF

echo "[5/7] Installing application files to /opt/win-a11y-shell..."
mkdir -p /opt/win-a11y-shell
cp -rf src/* /opt/win-a11y-shell/

cat << 'EOF' > /usr/local/bin/win-a11y-shell
#!/usr/bin/env bash
export DISPLAY=:0
export GTK_MODULES=gail:atk-bridge
export QT_ACCESSIBILITY=1
export NO_AT_BRIDGE=0
export ACCESSIBILITY_ENABLED=1
export GNOME_ACCESSIBILITY=1
python3 /opt/win-a11y-shell/daemon.py "$@"
EOF
chmod +x /usr/local/bin/win-a11y-shell

echo "[6/7] Configuring X11 Orca autostart (~/.xinitrc)..."
cat << 'EOF' > /root/.xinitrc
#!/usr/bin/env bash
export DISPLAY=:0

if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    eval $(dbus-launch --sh-syntax --exit-with-session)
fi

export GTK_MODULES=gail:atk-bridge
export QT_ACCESSIBILITY=1
export NO_AT_BRIDGE=0
export ACCESSIBILITY_ENABLED=1
export GNOME_ACCESSIBILITY=1

gsettings set org.gnome.desktop.interface toolkit-accessibility true || true
gsettings set org.gnome.desktop.a11y.applications screen-reader-enabled true || true

openbox &
orca --replace &
exec python3 /opt/win-a11y-shell/daemon.py
EOF
chmod +x /root/.xinitrc

echo "[7/7] Configuring nodm auto-login..."
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
echo "  INSTALLATION COMPLETE! ORCA & GNOME TERMINAL READY."
echo "=================================================="
