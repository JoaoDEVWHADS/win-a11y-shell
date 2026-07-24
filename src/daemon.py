#!/usr/bin/env python3
"""
win-a11y-shell Real-Time Daemon with SysTray & Desktop Window Integration
"""

import os
import sys
import time
import glob
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

from speech import SpeechEngine
from systray import SystemTray
from window import AccessibleShellWindow
from desktop import AccessibleDesktopWindow

try:
    import evdev
    from evdev import InputDevice, ecodes
except ImportError:
    pass

class RealtimeShellDaemon:
    def __init__(self):
        self.speech = SpeechEngine()
        self.systray = SystemTray(self.speech)
        self.systray_window = AccessibleShellWindow(self.speech, self.systray)
        self.desktop_window = AccessibleDesktopWindow(self.speech)
        self.super_pressed = False

    def trigger_systray_window(self):
        GLib.idle_add(self.systray_window.open_systray_window)

    def trigger_desktop_window(self):
        GLib.idle_add(self.desktop_window.open_desktop_window)

    def start(self):
        print("==================================================")
        print("  win-a11y-shell Daemon (Win+B / Win+M / Win+D Active)")
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
                                self.super_pressed = (event.value == 1 or event.value == 2)
                            elif event.value == 1 and self.super_pressed:
                                if event.code == ecodes.KEY_B:
                                    self.trigger_systray_window()
                                elif event.code in (ecodes.KEY_M, ecodes.KEY_D):
                                    self.trigger_desktop_window()
                except OSError:
                    pass

if __name__ == "__main__":
    daemon = RealtimeShellDaemon()
    daemon.start()
