import os
import subprocess
import shutil
import threading
import queue

class SpeechEngine:
    """
    Ultra-Robust Sound Synthesizer Engine for Linux Debian.
    Automatically resets ALSA audio hardware & unmutes channels on startup.
    """
    def __init__(self):
        self.espeak = shutil.which("espeak-ng") or shutil.which("espeak")
        self.speech_queue = queue.Queue(maxsize=3)
        
        # Auto-reset audio hardware on startup
        self.init_audio_hardware()

        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()

    def init_audio_hardware(self):
        """Automatic audio hardware reset & unmute procedure on daemon startup."""
        try:
            subprocess.run(["amixer", "set", "Master", "100%", "unmute"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["amixer", "set", "PCM", "100%", "unmute"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["alsactl", "restore"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def speak(self, text: str):
        if not text:
            return
            
        print(f"[SPEECH]: {text}")
        clean_text = text.replace('"', '').replace("'", "").strip()
        
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break

        try:
            self.speech_queue.put_nowait(clean_text)
        except queue.Full:
            pass

    def _speech_worker(self):
        while True:
            text = self.speech_queue.get()
            if self.espeak and text:
                try:
                    cmd = f'espeak-ng -v pt-br -s 175 "{text}" >/dev/null 2>&1'
                    subprocess.run(cmd, shell=True, timeout=3)
                except Exception:
                    pass
            self.speech_queue.task_done()
