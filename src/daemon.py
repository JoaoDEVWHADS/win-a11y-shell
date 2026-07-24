#!/usr/bin/env python3
"""
win-a11y-shell Real-Time Daemon
Hotkeys: Win+B (SysTray), Win+M / Win+D (Desktop), Ctrl+Alt+T (GNOME Terminal)
Auto-hides shell window when launching external apps so Orca reads external windows natively.
Resilient infinite supervisor loop preventing crash / termination.
"""

import os
import sys
import time
import glob
import subprocess
import threading
import fcntl
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

from speech import SpeechEngine
from shell_focus import WindowsFocusController

# Enforce single instance daemon using per-user file lock
try:
    uid = os.getuid()
    lock_file_path = f'/tmp/win_a11y_shell_{uid}.lock'
    lock_file = open(lock_file_path, 'w')
    fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except Exception:
    print("[ERROR] Another instance of win-a11y-shell daemon is already running. Exiting.")
    sys.exit(0)

try:
    import evdev
    from evdev import InputDevice, ecodes
except ImportError:
    pass

class RealtimeShellDaemon:
    def __init__(self):
        self.speech = SpeechEngine()
        self.controller = WindowsFocusController(self.speech)
        self.super_pressed = False
        self.ctrl_pressed = False
        self.alt_pressed = False
        self.shift_pressed = False

        self.evdev_thread = threading.Thread(target=self.evdev_loop, daemon=True)
        self.evdev_thread.start()

    def trigger_systray(self):
        GLib.idle_add(lambda: self.controller.focus_region('systray'))

    def trigger_desktop(self):
        GLib.idle_add(lambda: self.controller.focus_region('desktop'))

    def trigger_start(self):
        GLib.idle_add(lambda: self.controller.focus_region('start'))

    def trigger_terminal(self):
        GLib.idle_add(self._launch_terminal)

    def _launch_terminal(self):
        self.speech.speak("Abrindo GNOME Terminal")
        self.controller.hide()
        try:
            subprocess.Popen(["gnome-terminal"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[ERROR] Fail to launch terminal: {e}")

    def evdev_loop(self):
        while True:
            try:
                devices = []
                for path in glob.glob('/dev/input/event*'):
                    try:
                        dev = InputDevice(path)
                        capabilities = dev.capabilities()
                        if ecodes.EV_KEY in capabilities:
                            keys = capabilities[ecodes.EV_KEY]
                            if ecodes.KEY_A in keys or ecodes.KEY_ENTER in keys:
                                devices.append(dev)
                    except (PermissionError, OSError):
                        continue

                if not devices:
                    time.sleep(2)
                    continue

                import select
                dev_map = {dev.fd: dev for dev in devices}

                while dev_map:
                    r, _, _ = select.select(list(dev_map.keys()), [], [], 1.0)
                    for fd in r:
                        if fd not in dev_map:
                            continue
                        dev = dev_map[fd]
                        try:
                            for event in dev.read():
                                if event.type == ecodes.EV_KEY:
                                    if event.code in (ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT):
                                        self.shift_pressed = (event.value in (1, 2))
                                    elif event.code in (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL):
                                        self.ctrl_pressed = (event.value in (1, 2))
                                    elif event.code in (ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT):
                                        self.alt_pressed = (event.value in (1, 2))
                                    elif event.code in (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA):
                                        self.super_pressed = (event.value in (1, 2))
                                    
                                    elif event.value == 1:
                                        if self.super_pressed and event.code == ecodes.KEY_B:
                                            print("[DEBUG Daemon] Atalho detectado: Win+B (SysTray)", flush=True)
                                            self.trigger_systray()
                                        elif self.super_pressed and event.code in (ecodes.KEY_M, ecodes.KEY_D):
                                            print("[DEBUG Daemon] Atalho detectado: Win+M/D (Desktop)", flush=True)
                                            self.trigger_desktop()
                                        elif self.ctrl_pressed and self.alt_pressed and event.code == ecodes.KEY_T:
                                            print("[DEBUG Daemon] Atalho detectado: Ctrl+Alt+T (Terminal)", flush=True)
                                            self.trigger_terminal()
                                        elif (self.super_pressed and event.code == ecodes.KEY_O) or (self.ctrl_pressed and self.alt_pressed and event.code == ecodes.KEY_O):
                                            print("[DEBUG Daemon] Atalho detectado: Win+O (Preferências Orca)", flush=True)
                                            subprocess.Popen(["pkill", "-USR1", "-f", "python3 -m orca.orca"])
                                        elif event.code in (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA):
                                            print("[DEBUG Daemon] Atalho detectado: Super (Start Menu)", flush=True)
                                            self.trigger_start()
                        except Exception:
                            dev_map.pop(fd, None)
            except Exception:
                time.sleep(1)

def main():
    print("[WIN-A11Y-SHELL DAEMON] Server starting...")
    daemon = RealtimeShellDaemon()
    
    # Hide window on startup
    daemon.controller.hide()

    # Login window is NOT auto-opened on daemon restart.
    # It can be triggered externally or via a dedicated hotkey.

    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
