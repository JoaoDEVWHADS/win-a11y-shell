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

echo "[1/7] Purging console audio locks (espeakup) & configuring input permissions..."
apt-get purge -y espeakup 2>/dev/null || true

# Garantir permissoes de leitura nos dispositivos evdev (/dev/input) para todos os usuarios no grupo input
cat << 'EOF' > /etc/udev/rules.d/99-input-permissions.rules
KERNEL=="event*", NAME="input/%k", MODE="0660", GROUP="input"
EOF
udevadm control --reload-rules 2>/dev/null || true
udevadm trigger 2>/dev/null || true

# Adicionar todos os usuarios com UID >= 1000 ao grupo input
for u in $(getent passwd | awk -F: '$3 >= 1000 && $3 < 65534 {print $1}'); do
    usermod -aG input "$u" 2>/dev/null || true
done


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

if [ -f /etc/speech-dispatcher/speechd.conf ]; then
    sed -i 's/# AudioOutputMethod "pulse"/AudioOutputMethod "alsa"/' /etc/speech-dispatcher/speechd.conf || true
    sed -i 's/#AudioALSADevice "default"/AudioALSADevice "default"/' /etc/speech-dispatcher/speechd.conf || true
fi

echo "[3/7] Updating package lists..."
apt-get update -qq

echo "[4/7] Installing Orca, GNOME Terminal, GTK3 & Accessibility Packages..."
apt-get install -y -qq \
    locales \
    gettext \
    orca \
    gnome-terminal \
    python3-pyatspi \
    gir1.2-atspi-2.0 \
    dbus-x11 \
    libglib2.0-bin \
    speech-dispatcher \
    speech-dispatcher-audio-plugins \
    python3-speechd \
    espeak-ng \
    alsa-utils \
    xserver-xorg-core \
    xinit \
    openbox \
    x11-xserver-utils \
    x11-utils \
    xdotool \
    wmctrl \
    lightdm \
    python3 \
    python3-pip \
    python3-gi \
    gir1.2-gtk-3.0 \
    python3-evdev \
    python3-dasbus \
    python3-setproctitle \
    gsettings-desktop-schemas

sed -i 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen 2>/dev/null || true
locale-gen pt_BR.UTF-8 2>/dev/null || true
update-locale LANG=pt_BR.UTF-8 LC_ALL=pt_BR.UTF-8 2>/dev/null || true

cat << 'EOF' > /etc/environment
DISPLAY=:0
GTK_MODULES=gail:atk-bridge
QT_ACCESSIBILITY=1
NO_AT_BRIDGE=0
ACCESSIBILITY_ENABLED=1
GNOME_ACCESSIBILITY=1
VTE_CJK_WIDTH=1
LANG=pt_BR.UTF-8
LC_ALL=pt_BR.UTF-8
EOF

# Orca config will be written per-user at session start (see session script below)

# (Orca user-settings.py is written dynamically at session start for any user)


if [ -f /etc/speech-dispatcher/speechd.conf ]; then
    sed -i 's/# AudioOutputMethod "pulse"/AudioOutputMethod "alsa"/' /etc/speech-dispatcher/speechd.conf
    sed -i 's/AudioOutputMethod "pulse"/AudioOutputMethod "alsa"/' /etc/speech-dispatcher/speechd.conf
    sed -i 's/# DefaultLanguage "en-US"/DefaultLanguage "pt-BR"/' /etc/speech-dispatcher/speechd.conf
fi

echo "[5/7] Installing application files and embedded custom Orca..."
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p /opt/win-a11y-shell
cp -rf "$PROJECT_DIR"/src/* /opt/win-a11y-shell/
if [ -d "$PROJECT_DIR/orca" ]; then
    cp -rf "$PROJECT_DIR/orca" /opt/win-a11y-shell/
    mkdir -p /usr/share/locale/pt_BR/LC_MESSAGES /usr/share/locale/pt/LC_MESSAGES /usr/share/orca/ui
    if [ -f "$PROJECT_DIR/orca/po/pt_BR.po" ]; then
        msgfmt -o /usr/share/locale/pt_BR/LC_MESSAGES/orca.mo "$PROJECT_DIR/orca/po/pt_BR.po" 2>/dev/null || true
    fi
    if [ -f "$PROJECT_DIR/orca/po/pt.po" ]; then
        msgfmt -o /usr/share/locale/pt/LC_MESSAGES/orca.mo "$PROJECT_DIR/orca/po/pt.po" 2>/dev/null || true
    fi
    if [ -d "$PROJECT_DIR/orca/src/orca" ]; then
        cp -f "$PROJECT_DIR/orca/src/orca/"*.ui /usr/share/orca/ui/ 2>/dev/null || true
    fi
fi

cat << 'EOF' > /usr/local/bin/orca
#!/usr/bin/env bash
export DISPLAY=:0
export GTK_MODULES=gail:atk-bridge
export QT_ACCESSIBILITY=1
export NO_AT_BRIDGE=0
export ACCESSIBILITY_ENABLED=1
export GNOME_ACCESSIBILITY=1
export LANG=pt_BR.UTF-8
export LC_ALL=pt_BR.UTF-8
export LANGUAGE=pt_BR:pt

# Resolve dynamic path to embedded Orca
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "/opt/win-a11y-shell/orca/src" ]; then
    ORCA_DIR="/opt/win-a11y-shell/orca/src"
else
    ORCA_DIR="$(dirname "$SCRIPT_DIR")/win-a11y-shell/orca/src"
fi

export PYTHONPATH="$ORCA_DIR:$PYTHONPATH"
if [ "$1" = "-s" ] || [ "$1" = "--setup" ]; then
    exec python3 -m orca.orca_bin "$@"
elif [ "$1" = "--replace" ] || [ "$1" = "--no-daemon" ]; then
    exec python3 -m orca.orca "$@"
else
    while true; do
        python3 -m orca.orca --replace "$@"
        sleep 1
    done
fi
EOF
chmod +x /usr/local/bin/orca
cp -f /usr/local/bin/orca /usr/bin/orca 2>/dev/null || true

cat << 'EOF' > /usr/local/bin/win-a11y-shell
#!/usr/bin/env bash
export DISPLAY=:0
export GTK_MODULES=gail:atk-bridge
export QT_ACCESSIBILITY=1
export NO_AT_BRIDGE=0
export ACCESSIBILITY_ENABLED=1
export GNOME_ACCESSIBILITY=1
export LANG=pt_BR.UTF-8
export LC_ALL=pt_BR.UTF-8
export LANGUAGE=pt_BR:pt

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "/opt/win-a11y-shell" ]; then
    APP_DIR="/opt/win-a11y-shell"
else
    APP_DIR="$(dirname "$SCRIPT_DIR")/win-a11y-shell"
fi

export PYTHONPATH="$APP_DIR/orca/src:$PYTHONPATH"
while true; do
    python3 "$APP_DIR/daemon.py" "$@"
    sleep 1
done
EOF
chmod +x /usr/local/bin/win-a11y-shell

echo "[6/7] Registrando win-a11y-shell como sessão X (xsessions)..."

# Session script — roda como o usuário que logou (qualquer um, não root)
cat << 'ENDSESSION' > /usr/local/bin/win-a11y-shell-session
#!/usr/bin/env bash
# win-a11y-shell X session — started by lightdm after user login
# $HOME, $USER, $XDG_RUNTIME_DIR are already set correctly by lightdm/PAM

export DISPLAY="${DISPLAY:-:0}"
export GTK_MODULES=gail:atk-bridge
export QT_ACCESSIBILITY=1
export NO_AT_BRIDGE=0
export ACCESSIBILITY_ENABLED=1
export GNOME_ACCESSIBILITY=1
export LANG=pt_BR.UTF-8
export LC_ALL=pt_BR.UTF-8
export LANGUAGE=pt_BR:pt
export PYTHONPATH="/opt/win-a11y-shell/orca/src:$PYTHONPATH"

# Limpar bus de acessibilidade antigo do greeter (lightdm/105) se tiver herdado
unset AT_SPI_BUS_ADDRESS

if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    eval $(dbus-launch --sh-syntax --exit-with-session)
fi

# Write Orca config to the real user's home (not /root)
ORCA_CFG="$HOME/.config/orca"
mkdir -p "$ORCA_CFG"
cat << 'ORCACFG' > "$ORCA_CFG/user-settings.py"
import orca.settings
orca.settings.enableSpeech = True
orca.settings.speechServerFactory = "speechdispatcherfactory"
orca.settings.speechServerInfo = None
orca.settings.screenReaderKeyBindings = True
orca.settings.voices = {
    'default': {'established': False, 'rate': 50, 'gain': 10, 'pitch': 5, 'name': 'pt-br', 'lang': 'pt-br'},
    'uppercase': {'established': False, 'average-pitch': 7.0},
    'hyperlink': {'established': False}
}
orca.settings.enableKeyEcho = True
orca.settings.enableAlphabeticKeys = True
orca.settings.enableNumericKeys = True
orca.settings.enablePunctuationKeys = True
orca.settings.enableSpace = True
orca.settings.enableEchoByCharacter = True
orca.settings.enableModifierKeys = False
orca.settings.enableFunctionKeys = False
orca.settings.enableActionKeys = True
orca.settings.enableNavigationKeys = True
orca.settings.speakBlankLines = True
orca.settings.speakMultiCaseStringsAsWords = True
orca.settings.orcaModifierKeys = ["Insert", "KP_Insert", "Caps_Lock"]
orca.settings.speakCellCoordinates = False
orca.settings.speakCellSpan = False
orca.settings.speakCellHeaders = False
ORCACFG

gsettings set org.gnome.desktop.interface toolkit-accessibility true 2>/dev/null || true
gsettings set org.gnome.desktop.a11y.applications screen-reader-enabled true 2>/dev/null || true

# Matar instancias antigas do daemon ou lock residual
pkill -u "$USER" -f daemon.py 2>/dev/null || true
rm -f /tmp/win_a11y_shell.lock 2>/dev/null || true

openbox &
/usr/local/bin/orca --replace &
exec /usr/local/bin/win-a11y-shell
ENDSESSION
chmod +x /usr/local/bin/win-a11y-shell-session

# Register as an X session so lightdm shows it in the session list
mkdir -p /usr/share/xsessions
cat << 'EOF' > /usr/share/xsessions/win-a11y-shell.desktop
[Desktop Entry]
Name=win-a11y-shell
Comment=Accessible Windows-like Shell with Orca
Exec=/usr/local/bin/win-a11y-shell-session
Type=Application
EOF

echo "[7/7] Configurando lightdm como display manager padrão..."
# Desabilitar nodm se estiver instalado
systemctl disable nodm 2>/dev/null || true
systemctl stop nodm 2>/dev/null || true

# Instalar script de setup do greeter (inicia Orca na tela de login)
cp -f "$PROJECT_DIR/win-a11y-greeter-setup" /usr/local/bin/win-a11y-greeter-setup
chmod +x /usr/local/bin/win-a11y-greeter-setup

# Configurar lightdm — tela de login real com Orca acessível
mkdir -p /etc/lightdm
cat << 'EOF' > /etc/lightdm/lightdm.conf
[Seat:*]
user-session=win-a11y-shell
greeter-session=lightdm-gtk-greeter
greeter-setup-script=/usr/local/bin/win-a11y-greeter-setup
EOF

cat << 'EOF' > /etc/lightdm/lightdm-gtk-greeter.conf
[greeter]
a11y-states=+reader
reader=orca
indicators=~host;~spacer;~clock;~power;~a11y
active-monitor=0
EOF


# Habilitar e iniciar lightdm
systemctl enable lightdm 2>/dev/null || true
systemctl set-default graphical.target 2>/dev/null || true

echo "=================================================="
echo "  INSTALLATION COMPLETE!"
echo "  Display Manager: lightdm (tela de login)"
echo "  Sessão: win-a11y-shell (após login do usuário)"
echo "  Orca + daemon: iniciados automaticamente ao logar"
echo "  Reinicie o sistema para ativar: reboot"
echo "=================================================="
