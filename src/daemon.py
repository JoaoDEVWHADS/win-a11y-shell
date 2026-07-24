#!/usr/bin/env python3
"""
win-a11y-shell Real-Time Daemon
Hotkeys: Win+B (SysTray), Win+M / Win+D (Desktop), Ctrl+Alt+T (Terminal)
"""

import os
import sys
import glob
import subprocess
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

from speech import SpeechEngine
from shell_focus import WindowsFocusController

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

    def trigger_desktop(self):
        GLib.idle_add(lambda: self.controller.focus_region('desktop'))

    def trigger_systray(self):
        GLib.idle_add(lambda: self.controller.focus_region('systray'))

    def launch_terminal(self):
        self.speech.speak("Abrindo Terminal")
        env = os.environ.copy()
        env["DISPLAY"] = ":0"
        
        # Try lxterminal, xterm, or x-terminal-emulator
        for cmd in [["lxterminal"], ["xterm"], ["x-terminal-emulator"]]:
            try:
                subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                break
            except Exception:
                pass

    def start(self):
        print("==================================================")
        print("  win-a11y-shell Daemon Active")
        print("  Win+B (SysTray) | Win+M (Desktop) | Ctrl+Alt+T (Terminal)")
        print("==================================================")

        GLib.idle_add(self.listen_evdev)
        Gtk.main()

    def listen_evdev(self):
        import threading
        t = threading.Thread(target=self.evdev_loop, daemon=True)
        t.start()
        return False

    def evdev_loop(self):
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
            return

        import select
        dev_map = {dev.fd: dev for dev in devices}

        while True:
            r, _, _ = select.select(dev_map.keys(), [], [])
            for fd in r:
                dev = dev_map[fd]
                try:
                    for event in dev.read():
                        if event.type == ecodes.EV_KEY:
                            if event.code in (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA):
                                self.super_pressed = (event.value in (1, 2))
                            elif event.code in (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL):
                                self.ctrl_pressed = (event.value in (1, 2))
                            elif event.code in (ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT):
                                self.alt_pressed = (event.value in (1, 2))
                            
                            elif event.value == 1:
                                if self.super_pressed and event.code == ecodes.KEY_B:
                                    self.trigger_systray()
                                elif self.super_pressed and event.code in (ecodes.KEY_M, ecodes.KEY_D):
                                    self.trigger_desktop()
                                elif self.ctrl_pressed and self.alt_pressed and event.code == ecodes.KEY_T:
                                    GLib.idle_add(self.launch_terminal)
                except OSError:
                    pass

if __name__ == "__main__":
    daemon = RealtimeShellDaemon()
    daemon.start()
