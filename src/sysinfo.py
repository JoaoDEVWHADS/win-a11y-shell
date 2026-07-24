import subprocess
import datetime
import re


def _get_audio_card_name() -> str:
    """Return the real audio card name from ALSA."""
    try:
        res = subprocess.check_output(
            ["cat", "/proc/asound/card0/id"],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        if res:
            return res
    except Exception:
        pass
    return "Headphone"


def _get_master_info():
    """Return (volume_pct: int, is_muted: bool) from amixer Master."""
    try:
        res = subprocess.check_output(
            ["amixer", "get", "Master"],
            stderr=subprocess.DEVNULL
        ).decode('utf-8')
        match_vol = re.search(r'\[(\d+)%\]', res)
        muted = '[off]' in res
        vol = int(match_vol.group(1)) if match_vol else 100
        return vol, muted
    except Exception:
        return 100, False


def get_real_volume() -> str:
    """Return formatted volume string with real device name."""
    card = _get_audio_card_name()
    vol, muted = _get_master_info()
    status = f"{vol}%"
    return f"Volume {card}: {status}"


def get_volume_percent() -> int:
    vol, _ = _get_master_info()
    return vol


def get_mute_state() -> bool:
    _, muted = _get_master_info()
    return muted


def set_volume_percent(pct: int):
    """Set Master volume to pct (0-100)."""
    pct = max(0, min(100, pct))
    try:
        subprocess.run(
            ["amixer", "set", "Master", f"{pct}%"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
    except Exception:
        pass


def toggle_mute():
    """Toggle Master mute on/off."""
    try:
        subprocess.run(
            ["amixer", "set", "Master", "toggle"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
    except Exception:
        pass


def get_real_clock() -> str:
    now = datetime.datetime.now()
    return now.strftime("%H:%M %d/%m/%Y")


def get_real_network() -> str:
    try:
        route = subprocess.check_output(
            ["ip", "route", "show", "default"],
            stderr=subprocess.DEVNULL
        ).decode('utf-8')
        if "dev" in route:
            iface = route.split("dev")[1].split()[0]
            return f"Rede {iface} Acesso à Internet"
    except Exception:
        pass
    return "Rede Conectada Acesso à Internet"
