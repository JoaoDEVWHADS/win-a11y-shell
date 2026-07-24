import subprocess
import datetime
import re

def get_real_clock() -> str:
    now = datetime.datetime.now()
    return now.strftime("%H:%M %d/%m/%Y")

def get_real_volume() -> str:
    try:
        res = subprocess.check_output(["amixer", "get", "Master"], stderr=subprocess.DEVNULL).decode('utf-8')
        match = re.search(r'\[(\d+%)\]', res)
        if match:
            return f"Volume Headphone: {match.group(1)}"
    except Exception:
        pass
    return "Volume Headphone: 100%"

def get_real_network() -> str:
    try:
        # Check active default route
        route = subprocess.check_output(["ip", "route", "show", "default"], stderr=subprocess.DEVNULL).decode('utf-8')
        if "dev" in route:
            iface = route.split("dev")[1].split()[0]
            return f"Rede {iface} Acesso à Internet"
    except Exception:
        pass
    return "Rede Conectada Acesso à Internet"
