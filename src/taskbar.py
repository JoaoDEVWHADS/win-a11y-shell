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
                name = subprocess.check_output(["xdotool", "getwindowname", wid], stderr=subprocess.DEVNULL).decode('utf-8').strip()
                print(f"[DEBUG Taskbar] WID {wid} -> Titulo: '{name}'", flush=True)
                if name and name not in ("win-a11y-shell", "openbox", "Desktop", "Área de Trabalho") and "win-a11y-shell" not in name:
                    windows.append((wid, f"{name} - 1 janela em execução", idx, total))
            except Exception as e:
                print(f"[DEBUG Taskbar] Erro lendo nome da janela {wid}: {e}", flush=True)
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
            # Activate window focus
            res = subprocess.run(["xdotool", "windowactivate", "--sync", wid], check=False, stderr=subprocess.DEVNULL)
            print(f"[DEBUG ActivateWindow] xdotool windowactivate retorno: {res.returncode}", flush=True)
            if res.returncode != 0:
                # Fallback to wmctrl if xdotool fails
                res_wm = subprocess.run(["wmctrl", "-i", "-a", wid], check=False, stderr=subprocess.DEVNULL)
                print(f"[DEBUG ActivateWindow] wmctrl retorno: {res_wm.returncode}", flush=True)
        except Exception as e:
            print(f"[DEBUG ActivateWindow] Erro ao ativar janela: {e}", flush=True)
