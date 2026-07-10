from datetime import date

import numpy as np

from config import FATIGUE_SESSION_RISK_MINUTES, RECENT_INTENSITY_MINUTES


class FatigueModel:
    def __init__(self, stats_service):
        self.stats = stats_service

    @staticmethod
    def level(score):
        if score < 40:
            return "健康状态", "Green"
        if score < 70:
            return "轻度负荷", "Yellow"
        if score < 85:
            return "高负荷", "Orange"
        return "危险状态，必须休息", "Red"

    def calculate(self):
        today_total = self.stats.total_keys_for_date(date.today())
        seven_mean, _ = self.stats.seven_day_mean_std()
        baseline = max(seven_mean, 1.0)
        total_factor = min(today_total / baseline, 2.5) / 2.5

        recent_keys_per_min = self.stats.recent_intensity(RECENT_INTENSITY_MINUTES)
        recent_factor = min(recent_keys_per_min / 120.0, 1.0)

        sessions = self.stats.session_lengths(1)
        longest_session = float(sessions["minutes"].max()) if not sessions.empty else 0.0
        session_factor = min(longest_session / FATIGUE_SESSION_RISK_MINUTES, 1.0)

        trend = self.stats.rolling_daily_stats(7)
        mean = max(float(trend["total_keys"].mean()), 1.0)
        volatility_factor = min(float(np.std(trend["total_keys"]) / mean), 1.0)

        score = (
            total_factor * 40
            + recent_factor * 30
            + session_factor * 20
            + volatility_factor * 10
        )
        score = float(max(0, min(100, score)))
        label, color = self.level(score)
        return {
            "score": score,
            "level": label,
            "color": color,
            "components": {
                "total_factor": total_factor * 40,
                "recent_intensity_factor": recent_factor * 30,
                "longest_session_factor": session_factor * 20,
                "volatility_factor": volatility_factor * 10,
            },
            "longest_session_minutes": longest_session,
            "recent_keys_per_min": recent_keys_per_min,
        }

