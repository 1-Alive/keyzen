from datetime import date, timedelta

from config import FATIGUE_SESSION_RISK_MINUTES, HIGH_INTENSITY_KEYS_PER_MIN


class AnomalyDetector:
    def __init__(self, stats_service):
        self.stats = stats_service

    def detect(self):
        anomalies = []
        today_total = self.stats.total_keys_for_date(date.today())
        mean, std = self.stats.seven_day_mean_std()

        if mean > 0 and today_total > mean + 2 * std:
            anomalies.append({
                "type": "异常高负荷",
                "message": f"今日键盘量 {today_total} 已超过 7 日均值 + 2σ ({mean + 2 * std:.0f})。",
                "severity": "high",
            })

        sessions = self.stats.session_lengths(1)
        risky = sessions[sessions["minutes"] > FATIGUE_SESSION_RISK_MINUTES] if not sessions.empty else sessions
        for row in risky.itertuples():
            speed = row.total_keys / max(row.minutes, 1)
            if speed >= HIGH_INTENSITY_KEYS_PER_MIN:
                anomalies.append({
                    "type": "疲劳风险",
                    "message": f"连续高强度输入 {row.minutes:.0f} 分钟，平均 {speed:.0f} keys/min。",
                    "severity": "critical",
                })

        yesterday = self.stats.total_keys_for_date(date.today() - timedelta(days=1))
        if mean > 0 and yesterday >= mean * 0.7 and today_total < mean * 0.35:
            anomalies.append({
                "type": "低活跃异常",
                "message": f"今日键盘量明显低于近期水平：{today_total} vs 7 日均值 {mean:.0f}。",
                "severity": "medium",
            })
        return anomalies

