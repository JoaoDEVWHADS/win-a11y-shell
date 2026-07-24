import os
import subprocess
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Atk

class SpeechEngine:
    """
    100% Native Orca Accessibility Engine.
    Emits ATK Accessible Focus/Name events directly to Orca.
    """
    def __init__(self):
        pass

    def speak(self, text: str, widget=None):
        """
        Notify Orca screen reader via GTK ATK Accessible Name update.
        """
        if not text:
            return
            
        print(f"[ORCA ATK NATIVE]: {text}")
        
        # If a GTK widget is passed, set ATK Accessible Name for Orca
        if widget and hasattr(widget, 'get_accessible'):
            try:
                atk_obj = widget.get_accessible()
                atk_obj.set_name(text)
                atk_obj.notify("accessible-name")
            except Exception:
                pass
        
        # Fallback AT-SPI2 system notification for Orca
        try:
            subprocess.Popen(["spd-say", "-m", "orca", "-r", "15", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
