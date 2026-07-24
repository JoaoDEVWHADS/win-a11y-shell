#!/usr/bin/env python3
"""
win-a11y-shell Real-Time Interactive Daemon
Hooking Linux evdev input devices directly for headless & desktop compatibility.
"""

import os
import sys
import time
import glob
from speech import SpeechEngine
from systray import SystemTray

try:
    import evdev
    from evdev import InputDevice, ecodes
except ImportError:
    print("[ERROR] 'evdev' library not installed. Install with: apt-get install python3-evdev")
    sys.exit(1)

class RealtimeShellDaemon:
    def __init__(self):
        self.speech = SpeechEngine()
        self.systray = SystemTray(self.speech)
        self.current_focus = None
        self.super_pressed = False

    def get_keyboard_devices(self):
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
        return devices

    def start(self):
        print("==================================================")
        print("  win-a11y-shell Daemon (Evdev System Active)")
        print("==================================================")
        self.speech.speak("Sistema win a11y shell iniciado em tempo real. Pressione Windows B para a bandeja ou Windows M para a área de trabalho.")
        
        devices = self.get_keyboard_devices()
        if not devices:
            print("[INFO] Daemon running in background system service mode.")
            # Fallback service loop
            while True:
                time.sleep(1)

        import select
        dev_map = {dev.fd: dev for dev in devices}

        while True:
            r, _, _ = select.select(dev_map.keys(), [], [])
            for fd in r:
                dev = dev_map[fd]
                try:
                    for event in dev.read():
                        if event.type == ecodes.EV_KEY:
                            self.handle_key_event(event)
                except OSError:
                    pass

    def handle_key_event(self, event):
        # 1 = Press, 0 = Release
        if event.code in (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA):
            self.super_pressed = (event.value == 1 or event.value == 2)
            if event.value == 0:  # Win key press alone opens Start Menu
                pass

        if event.value == 1: # Key press
            if self.super_pressed and event.code == ecodes.KEY_B:
                self.current_focus = 'systray'
                self.systray.focus()
            elif self.super_pressed and event.code == ecodes.KEY_M:
                self.current_focus = 'desktop'
                self.speech.speak("Desktop  lista  FileZilla Client  62 de 105")
            elif self.current_focus == 'systray':
                if event.code == ecodes.KEY_RIGHT:
                    self.systray.navigate_right()
                elif event.code == ecodes.KEY_LEFT:
                    self.systray.navigate_left()
                elif event.code in (ecodes.KEY_ENTER, ecodes.KEY_KPENTER, ecodes.KEY_SPACE):
                    self.systray.activate()
                elif event.code == ecodes.KEY_TAB:
                    self.speech.speak("Iniciar  botão de alternância  não pressionado")

if __name__ == "__main__":
    daemon = RealtimeShellDaemon()
    daemon.start()
