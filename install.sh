#!/usr/bin/env bash
# ==============================================================================
# win-a11y-shell Complete Automatic Installer & Audio Fix
# ==============================================================================

set -e

echo "=================================================="
echo "  Installing win-a11y-shell (Debian Accessibility)"
echo "=================================================="

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root (sudo ./install.sh)"
  exit 1
fi

echo "[1/6] Purging audio-locking console services (espeakup)..."
apt-get purge -y espeakup 2>/dev/null || true

echo "[2/6] Configuring ALSA Shared Audio (dmix) in /etc/asound.conf..."
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

echo "[3/6] Installing Xorg minimal display server & Openbox..."
apt-get update -qq
apt-get install -y -qq \
    xserver-xorg-core \
    xinit \
    openbox \
    x11-xserver-utils \
    x11-utils \
    xdotool \
    nodm

echo "[4/6] Installing GTK3 & Speech dependencies..."
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-gi \
    gir1.2-gtk-3.0 \
    speech-dispatcher \
    python3-speechd \
    espeak-ng \
    python3-evdev \
    alsa-utils

echo "[5/6] Installing application files..."
mkdir -p /opt/win-a11y-shell
cp -rf src/* /opt/win-a11y-shell/

cat << 'EOF' > /usr/local/bin/win-a11y-shell
#!/usr/bin/env bash
export DISPLAY=:0
python3 /opt/win-a11y-shell/daemon.py "$@"
EOF
chmod +x /usr/local/bin/win-a11y-shell

echo "[6/6] Configuring autostart (~/.xinitrc & nodm)..."
cat << 'EOF' > /root/.xinitrc
#!/usr/bin/env bash
openbox &
python3 /opt/win-a11y-shell/daemon.py
EOF
chmod +x /root/.xinitrc

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
echo "  INSTALLATION & AUDIO LOCK PREVENTION COMPLETE!"
echo "=================================================="
