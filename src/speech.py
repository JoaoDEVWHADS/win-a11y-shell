import os
import subprocess
import shutil
import threading
import queue

class SpeechEngine:
    """
    Ultra-Robust Sound Synthesizer Engine for Linux Debian.
    Uses non-blocking shell subprocesses to avoid ALSA driver locks.
    """
    def __init__(self):
        self.espeak = shutil.which("espeak-ng") or shutil.which("espeak")
        self.speech_queue = queue.Queue(maxsize=3)
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()

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
                    # Run espeak-ng through shell command with timeout
                    cmd = f'espeak-ng -v pt-br -s 175 "{text}" >/dev/null 2>&1'
                    subprocess.run(cmd, shell=True, timeout=3)
                except Exception:
                    pass
            self.speech_queue.task_done()
