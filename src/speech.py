import os
import subprocess
import shutil

class SpeechEngine:
    """
    Speech Engine interface for Debian Accessibility.
    Uses direct espeak-ng / spd-say with fallback for instant audio output.
    """
    def __init__(self):
        self.espeak = shutil.which("espeak-ng") or shutil.which("espeak")
        self.spd = shutil.which("spd-say")

    def speak(self, text: str):
        """Announce text via espeak-ng or speech-dispatcher."""
        print(f"[SPEECH]: {text}")
        
        # Clean text for command line
        clean_text = text.replace('"', '').replace("'", "")
        
        if self.espeak:
            try:
                subprocess.Popen([self.espeak, "-v", "pt-br", "-s", "170", clean_text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except Exception:
                pass

        if self.spd:
            try:
                subprocess.Popen(["spd-say", "-l", "pt-br", "-r", "15", clean_text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
