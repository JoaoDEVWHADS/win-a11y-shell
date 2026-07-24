import subprocess

def get_running_windows():
    """
    Fetch REAL open X11 windows in Linux using xdotool.
    """
    windows = []
    try:
        res = subprocess.check_output(["xdotool", "search", "--onlyvisible", "--class", "."], stderr=subprocess.DEVNULL).decode('utf-8')
        wids = [w.strip() for w in res.splitlines() if w.strip()]
        
        total = len(wids)
        for idx, wid in enumerate(wids, start=1):
            try:
                name = subprocess.check_output(["xdotool", "getwindowname", wid], stderr=subprocess.DEVNULL).decode('utf-8').strip()
                if name and name not in ("win-a11y-shell", "openbox"):
                    windows.append((wid, f"{name} - 1 janela em execução", idx, total))
            except Exception:
                pass
    except Exception:
        pass

    if not windows:
        windows.append(("0", "Nenhuma janela em execução", 1, 1))

    return windows

def activate_window(wid: str):
    """
    Switch focus directly to selected Linux window.
    """
    if wid and wid != "0":
        try:
            subprocess.run(["xdotool", "windowactivate", wid], check=False)
        except Exception:
            pass
