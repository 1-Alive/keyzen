from datetime import datetime, timedelta
from uuid import uuid4

from config import ACTIVE_WINDOW_SECONDS, SESSION_IDLE_MINUTES


class SessionManager:
    def __init__(self, db, idle_minutes=SESSION_IDLE_MINUTES):
        self.db = db
        self.idle_delta = timedelta(minutes=idle_minutes)
        self.current_session_id = None
        self.session_start = None
        self.last_input_time = None

    def resolve_session(self, now=None):
        now = now or datetime.now()
        if (
            self.current_session_id is None
            or self.last_input_time is None
            or now - self.last_input_time > self.idle_delta
        ):
            self.current_session_id = now.strftime("%Y%m%d%H%M%S") + "-" + uuid4().hex[:8]
            self.session_start = now
            self.db.ensure_session(self.current_session_id, now)
        self.last_input_time = now
        return self.current_session_id

    def is_active(self, now=None):
        now = now or datetime.now()
        return bool(self.last_input_time and now - self.last_input_time <= timedelta(seconds=ACTIVE_WINDOW_SECONDS))

