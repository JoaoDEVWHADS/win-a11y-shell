import os
import subprocess
import shutil
import threading
import queue

try:
    import speechd
except ImportError:
    speechd = None

class SpeechEngine:
    """
    Native Orca & Speech-Dispatcher Engine for win-a11y-shell.
    All announcements are sent natively to Orca's speech engine (speech-dispatcher).
    """
    def __init__(self):
        self.client = None
        self.speech_queue = queue.Queue(maxsize=5)
        
        self.init_speech_dispatcher()

        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()

    def init_speech_dispatcher(self):
        """Connect directly to Orca's speech-dispatcher client socket."""
        if speechd:
            try:
                self.client = speechd.Speaker("win-a11y-shell", "orca")
                self.client.set_language("pt-br")
                self.client.set_rate(15)
            except Exception:
                self.client = None

    def speak(self, text: str):
        """Announce text natively through Orca's speech channel."""
        if not text:
            return
            
        print(f"[ORCA SPEECH]: {text}")
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
            if text:
                spoken = False
                # 1. Primary: Orca speech-dispatcher connection
                if self.client:
                    try:
                        self.client.cancel()
                        self.client.speak(text)
                        spoken = True
                    except Exception:
                        self.init_speech_dispatcher()

                # 2. Fallback: spd-say Orca channel
                if not spoken:
                    try:
                        subprocess.run(["spd-say", "-l", "pt-br", "-r", "15", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
                        spoken = True
                    except Exception:
                        pass

                # 3. Fallback: espeak-ng WAV direct stream
                if not spoken:
                    try:
                        wav_file = "/tmp/orca_speech.wav"
                        subprocess.run(["espeak-ng", "-v", "pt-br", "-s", "175", text, "-w", wav_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
                        if os.path.exists(wav_file):
                            subprocess.run(["aplay", "-q", wav_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
                    except Exception:
                        pass

            self.speech_queue.task_done()
