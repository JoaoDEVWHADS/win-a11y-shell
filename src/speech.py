import os
import subprocess
import shutil
import threading
import queue

class SpeechEngine:
    """
    Thread-safe Queue-based Speech Engine for win-a11y-shell.
    Prevents ALSA buffer locks and process defunct zombies.
    """
    def __init__(self):
        self.espeak = shutil.which("espeak-ng") or shutil.which("espeak")
        self.speech_queue = queue.Queue(maxsize=5)
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()

    def speak(self, text: str):
        """Enqueue speech item, dropping old stacked items to keep speech instant."""
        if not text:
            return
            
        print(f"[SPEECH]: {text}")
        clean_text = text.replace('"', '').replace("'", "").strip()
        
        # Clear backlog if user is navigating fast
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
                    # Execute espeak-ng with timeout to prevent zombie process locks
                    subprocess.run(
                        [self.espeak, "-v", "pt-br", "-s", "170", text],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=4
                    )
                except (subprocess.TimeoutExpired, Exception):
                    pass
            self.speech_queue.task_done()
