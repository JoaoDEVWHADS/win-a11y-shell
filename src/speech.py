import subprocess
import shutil

class SpeechEngine:
    """
    Speech Engine interface for AT-SPI2 / Speech-Dispatcher or fallback stdout.
    Outputs announcements formatted exactly like NVDA screen reader.
    """
    def __init__(self):
        self.spd = shutil.which("spd-say")

    def speak(self, text: str):
        """Announce text via speech-dispatcher or print log."""
        print(f"[SPEECH]: {text}")
        if self.spd:
            try:
                subprocess.run(["spd-say", "-r", "15", text], check=False)
            except Exception:
                pass
