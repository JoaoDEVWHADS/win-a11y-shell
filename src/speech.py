import os
import subprocess

class SpeechEngine:
    """
    Unified Speech Dispatcher Engine for win-a11y-shell & Orca integration.
    Uses Speech Dispatcher (spd-say) so shell speech matches Orca screen reader audio natively.
    """
    def __init__(self):
        pass

    def interrupt(self):
        try:
            subprocess.Popen(["spd-say", "-S"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def speak(self, text: str, widget=None):
        if not text:
            return
            
        print(f"[WIN-A11Y LOG]: {text}")
        clean_text = text.replace('"', '').replace("'", "").strip()
        
        try:
            subprocess.Popen(
                ["spd-say", "-e", "-v", "pt-br", clean_text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass
