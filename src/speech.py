import os
import subprocess
import shutil
import threading
import queue

class SpeechEngine:
    """
    Direct Audio Synthesizer Pipeline for Orca and Accessible System Announcements.
    Ensures immediate portuguese audio feedback on any Debian setup.
    """
    def __init__(self):
        self.espeak = shutil.which("espeak-ng") or shutil.which("espeak")
        self.aplay = shutil.which("aplay")
        self.speech_queue = queue.Queue(maxsize=3)

        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()

    def speak(self, text: str, widget=None):
        if not text:
            return
            
        print(f"[SPEECH ANNOUNCEMENT]: {text}")
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
        wav_file = "/tmp/win_a11y_speech.wav"
        while True:
            text = self.speech_queue.get()
            if text and self.espeak:
                try:
                    subprocess.run(
                        [self.espeak, "-v", "pt-br", "-s", "175", text, "-w", wav_file],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=2
                    )
                    if self.aplay and os.path.exists(wav_file):
                        subprocess.run(
                            [self.aplay, "-q", wav_file],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=2
                        )
                except Exception:
                    pass
            self.speech_queue.task_done()
