import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta

from config import DB_PATH


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = str(db_path)
        self._lock = threading.RLock()
        self.init_db()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self):
        with self._lock, self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    total_keys INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS key_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );

                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    total_keys INTEGER NOT NULL DEFAULT 0,
                    avg_speed REAL NOT NULL DEFAULT 0,
                    fatigue_score REAL NOT NULL DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_key_log_ts ON key_log(ts);
                CREATE INDEX IF NOT EXISTS idx_key_log_session ON key_log(session_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time);
                CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date);
                """
            )

    def ensure_session(self, session_id, start_time):
        with self._lock, self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO sessions(session_id, start_time, end_time, total_keys)
                VALUES (?, ?, ?, 0)
                """,
                (session_id, start_time.isoformat(timespec="seconds"), start_time.isoformat(timespec="seconds")),
            )

    def insert_key(self, key, ts, session_id):
        ts_text = ts.isoformat(timespec="seconds")
        date_text = ts.date().isoformat()
        with self._lock, self.connect() as conn:
            conn.execute(
                "INSERT INTO key_log(key, ts, session_id) VALUES (?, ?, ?)",
                (key, ts_text, session_id),
            )
            conn.execute(
                """
                UPDATE sessions
                SET end_time = ?, total_keys = total_keys + 1
                WHERE session_id = ?
                """,
                (ts_text, session_id),
            )
            conn.execute(
                """
                INSERT INTO daily_stats(date, total_keys, avg_speed, fatigue_score)
                VALUES (?, 1, 0, 0)
                ON CONFLICT(date) DO UPDATE SET total_keys = total_keys + 1
                """,
                (date_text,),
            )

    def fetch_df(self, query, params=()):
        import pandas as pd

        with self._lock, sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)

    def execute(self, query, params=()):
        with self._lock, self.connect() as conn:
            conn.execute(query, params)

    def query_one(self, query, params=()):
        with self._lock, self.connect() as conn:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else None

    def query_all(self, query, params=()):
        with self._lock, self.connect() as conn:
            return [dict(row) for row in conn.execute(query, params).fetchall()]

    def update_daily_stats(self, target_date=None, fatigue_score=0):
        target_date = target_date or datetime.now().date()
        date_text = target_date.isoformat()
        start = datetime.combine(target_date, datetime.min.time())
        end = start + timedelta(days=1)
        with self._lock, self.connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM key_log WHERE ts >= ? AND ts < ?",
                (start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")),
            ).fetchone()[0]
            span = conn.execute(
                """
                SELECT MIN(ts), MAX(ts)
                FROM key_log
                WHERE ts >= ? AND ts < ?
                """,
                (start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")),
            ).fetchone()
            avg_speed = 0.0
            if span and span[0] and span[1] and total:
                minutes = max(
                    (datetime.fromisoformat(span[1]) - datetime.fromisoformat(span[0])).total_seconds() / 60,
                    1,
                )
                avg_speed = total / minutes
            conn.execute(
                """
                INSERT INTO daily_stats(date, total_keys, avg_speed, fatigue_score)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE
                SET total_keys = excluded.total_keys,
                    avg_speed = excluded.avg_speed,
                    fatigue_score = excluded.fatigue_score
                """,
                (date_text, total, avg_speed, float(fatigue_score)),
            )

