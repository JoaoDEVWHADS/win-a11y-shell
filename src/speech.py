import os
import subprocess
import shutil

class SpeechEngine:
    """
    Deduplicated Single-Voice Speech Engine for win-a11y-shell.
    Prevents duplicate voices by ensuring a single speech output channel.
    """
    def __init__(self):
        self.espeak = shutil.which("espeak-ng") or shutil.which("espeak")
        self.current_process = None

    def speak(self, text: str):
        """Announce text clearly without duplicate voices."""
        if not text:
            return
            
        print(f"[SPEECH]: {text}")
        clean_text = text.replace('"', '').replace("'", "")
        
        # Kill previous speech process if still playing to prevent overlap/voice stacking
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
            except Exception:
                pass

        if self.espeak:
            try:
                self.current_process = subprocess.Popen(
                    [self.espeak, "-v", "pt-br", "-s", "170", clean_text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception:
                pass
