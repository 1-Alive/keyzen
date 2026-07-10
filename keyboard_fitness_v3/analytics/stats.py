from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd


class StatsService:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _day_bounds(day):
        start = datetime.combine(day, datetime.min.time())
        end = start + timedelta(days=1)
        return start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")

    def total_keys_for_date(self, day=None):
        day = day or date.today()
        start, end = self._day_bounds(day)
        row = self.db.query_one("SELECT COUNT(*) AS c FROM key_log WHERE ts >= ? AND ts < ?", (start, end))
        return int(row["c"] if row else 0)

    def current_speed(self, minutes=1):
        end = datetime.now()
        start = end - timedelta(minutes=minutes)
        row = self.db.query_one(
            "SELECT COUNT(*) AS c FROM key_log WHERE ts >= ? AND ts <= ?",
            (start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")),
        )
        return int(row["c"] if row else 0) / max(minutes, 1)

    def recent_intensity(self, minutes=60):
        return self.current_speed(minutes=minutes)

    def fastest_speed_today(self, day=None):
        day = day or date.today()
        start, end = self._day_bounds(day)
        row = self.db.query_one(
            """
            SELECT MAX(minute_total) AS fastest
            FROM (
                SELECT strftime('%Y-%m-%d %H:%M', ts) AS minute_bucket,
                       COUNT(*) AS minute_total
                FROM key_log
                WHERE ts >= ? AND ts < ?
                GROUP BY minute_bucket
            )
            """,
            (start, end),
        )
        return int(row["fastest"] or 0) if row else 0

    def rolling_daily_stats(self, days=7, end_day=None):
        end_day = end_day or date.today()
        start_day = end_day - timedelta(days=days - 1)
        df = self.db.fetch_df(
            """
            SELECT date, total_keys, avg_speed, fatigue_score
            FROM daily_stats
            WHERE date >= ? AND date <= ?
            ORDER BY date
            """,
            (start_day.isoformat(), end_day.isoformat()),
        )
        all_days = pd.date_range(start_day, end_day, freq="D").strftime("%Y-%m-%d")
        if df.empty:
            return pd.DataFrame({"date": all_days, "total_keys": 0, "avg_speed": 0.0, "fatigue_score": 0.0})
        return (
            pd.DataFrame({"date": all_days})
            .merge(df, on="date", how="left")
            .fillna({"total_keys": 0, "avg_speed": 0.0, "fatigue_score": 0.0})
        )

    def seven_day_mean_std(self):
        df = self.rolling_daily_stats(7, date.today() - timedelta(days=1))
        values = df["total_keys"].astype(float).to_numpy()
        return float(np.mean(values)) if len(values) else 0.0, float(np.std(values)) if len(values) else 0.0

    def hourly_counts(self, day=None):
        day = day or date.today()
        start, end = self._day_bounds(day)
        df = self.db.fetch_df(
            """
            SELECT strftime('%H', ts) AS hour, COUNT(*) AS total
            FROM key_log
            WHERE ts >= ? AND ts < ?
            GROUP BY hour
            ORDER BY hour
            """,
            (start, end),
        )
        base = pd.DataFrame({"hour": list(range(24))})
        if not df.empty:
            df["hour"] = df["hour"].astype(int)
            base = base.merge(df, on="hour", how="left")
        else:
            base["total"] = 0
        base["total"] = base["total"].fillna(0).astype(int)
        return base

    def key_counts(self, day=None, limit=None):
        day = day or date.today()
        start, end = self._day_bounds(day)
        limit_clause = "LIMIT ?" if limit else ""
        params = [start, end]
        if limit:
            params.append(int(limit))
        return self.db.fetch_df(
            f"""
            SELECT key, COUNT(*) AS total
            FROM key_log
            WHERE ts >= ? AND ts < ?
            GROUP BY key
            ORDER BY total DESC, key ASC
            {limit_clause}
            """,
            tuple(params),
        )

    def session_lengths(self, days=30):
        start = datetime.now() - timedelta(days=days)
        df = self.db.fetch_df(
            """
            SELECT session_id, start_time, end_time, total_keys
            FROM sessions
            WHERE start_time >= ?
            ORDER BY start_time
            """,
            (start.isoformat(timespec="seconds"),),
        )
        if df.empty:
            return pd.DataFrame(columns=["session_id", "start_time", "end_time", "total_keys", "minutes"])
        df["start_time"] = pd.to_datetime(df["start_time"])
        df["end_time"] = pd.to_datetime(df["end_time"])
        df["minutes"] = (df["end_time"] - df["start_time"]).dt.total_seconds().clip(lower=0) / 60
        return df

    def today_summary(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        today_total = self.total_keys_for_date(today)
        yesterday_total = self.total_keys_for_date(yesterday)
        seven_mean, seven_std = self.seven_day_mean_std()
        return {
            "today_total": today_total,
            "yesterday_total": yesterday_total,
            "delta_vs_yesterday": today_total - yesterday_total,
            "seven_day_mean": seven_mean,
            "seven_day_std": seven_std,
            "current_speed": self.current_speed(1),
            "fastest_speed": self.fastest_speed_today(today),
        }
