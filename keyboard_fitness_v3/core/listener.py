from datetime import datetime
from threading import Thread

try:
    from pynput import keyboard
except ImportError:  # Allows analysis/reporting modules to run before dependencies are installed.
    keyboard = None


class KeyboardListener:
    def __init__(self, db, session_manager):
        self.db = db
        self.session_manager = session_manager
        self.listener = None
        self.enabled = False

    @staticmethod
    def normalize_key(key):
        try:
            return key.char if key.char else str(key)
        except AttributeError:
            return str(key)

    def _on_press(self, key):
        now = datetime.now()
        session_id = self.session_manager.resolve_session(now)
        self.db.insert_key(self.normalize_key(key), now, session_id)

    def start(self):
        if keyboard is None:
            raise RuntimeError("pynput is not installed. Run: pip install -r requirements.txt")
        if self.enabled:
            return
        self.enabled = True
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.daemon = True
        self.listener.start()

    def stop(self):
        self.enabled = False
        if self.listener:
            self.listener.stop()
            self.listener = None

    def start_in_thread(self):
        thread = Thread(target=self.start, daemon=True)
        thread.start()
        return thread

