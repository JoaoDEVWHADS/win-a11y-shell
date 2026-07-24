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
        print(f"[DEBUG Taskbar] Janelas brutas encontradas pelo xdotool: {wids}", flush=True)
        for idx, wid in enumerate(wids, start=1):
            try:
                wm_class = subprocess.check_output(["xprop", "-id", wid, "WM_CLASS"], stderr=subprocess.DEVNULL).decode('utf-8').lower()
                # Skip internal win-a11y-shell daemon and openbox windows
                if "daemon.py" in wm_class or "openbox" in wm_class:
                    continue
                
                name = subprocess.check_output(["xdotool", "getwindowname", wid], stderr=subprocess.DEVNULL).decode('utf-8').strip()
                if not name:
                    if "gnome-terminal" in wm_class:
                        name = "GNOME Terminal"
                    elif "orca" in wm_class:
                        name = "Preferências do Orca"
                    else:
                        name = "Janela sem título"

                print(f"[DEBUG Taskbar] External WID {wid} -> Titulo: '{name}', Class: '{wm_class.strip()}'", flush=True)
                windows.append((wid, f"{name} - 1 janela em execução", idx, total))
            except Exception as e:
                print(f"[DEBUG Taskbar] Erro lendo dados da janela {wid}: {e}", flush=True)
    except Exception as e:
        print(f"[DEBUG Taskbar] Erro buscando janelas com xdotool: {e}", flush=True)

    if not windows:
        windows.append(("0", "Nenhuma janela em execução", 1, 1))

    print(f"[DEBUG Taskbar] Janelas filtradas para a barra de tarefas: {windows}", flush=True)
    return windows

def activate_window(wid: str):
    """
    Switch focus directly to selected Linux window.
    """
    print(f"[DEBUG ActivateWindow] Tentando ativar janela WID: {wid}", flush=True)
    if wid and wid != "0":
        try:
            # Map/unminimize first if minimized
            subprocess.run(["xdotool", "windowmap", wid], check=False, stderr=subprocess.DEVNULL)
            # Activate window focus via xdotool and wmctrl in parallel for modal/dialog windows
            subprocess.run(["xdotool", "windowactivate", "--sync", wid], check=False, stderr=subprocess.DEVNULL)
            subprocess.run(["wmctrl", "-i", "-a", wid], check=False, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[DEBUG ActivateWindow] Erro ao ativar janela: {e}", flush=True)
