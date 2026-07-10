import numpy as np


class TrendAnalyzer:
    def __init__(self, stats_service):
        self.stats = stats_service

    def seven_day_trend(self):
        return self.stats.rolling_daily_stats(7)

    def thirty_day_trend(self):
        return self.stats.rolling_daily_stats(30)

    def peak_hours(self, top_n=3):
        hourly = self.stats.hourly_counts()
        if hourly.empty:
            return []
        rows = hourly.sort_values("total", ascending=False).head(top_n)
        return [f"{int(row.hour):02d}:00" for row in rows.itertuples() if row.total > 0]

    def low_activity_periods(self):
        hourly = self.stats.hourly_counts()
        active = hourly[hourly["total"] > 0]
        if active.empty:
            return []
        threshold = float(np.percentile(active["total"], 25))
        return [f"{int(row.hour):02d}:00" for row in active.itertuples() if row.total <= threshold]

    def session_distribution(self):
        return self.stats.session_lengths(30)

