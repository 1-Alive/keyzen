from datetime import date

from config import REPORT_DIR
from gui.charts import make_dashboard_figure
from reporting.html_report import render_html


class ReportGenerator:
    def __init__(self, stats_service, fatigue_model, anomaly_detector, trend_analyzer):
        self.stats = stats_service
        self.fatigue = fatigue_model
        self.anomalies = anomaly_detector
        self.trends = trend_analyzer
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _display_key(key):
        names = {
            "Key.space": "Space",
            "Key.enter": "Enter",
            "Key.backspace": "Backspace",
            "Key.tab": "Tab",
            "Key.shift": "Shift",
            "Key.shift_r": "Right Shift",
            "Key.ctrl_l": "Ctrl",
            "Key.ctrl_r": "Right Ctrl",
            "Key.alt_l": "Alt",
            "Key.alt_r": "Right Alt",
            "Key.cmd": "Win/Cmd",
            "Key.esc": "Esc",
            "Key.delete": "Delete",
            "Key.up": "Arrow Up",
            "Key.down": "Arrow Down",
            "Key.left": "Arrow Left",
            "Key.right": "Arrow Right",
        }
        return names.get(str(key), str(key))

    def _top_key_summary(self):
        total = max(self.stats.total_keys_for_date(), 1)
        rows = self.stats.key_counts(limit=10)
        result = []
        for row in rows.itertuples():
            result.append({
                "key": self._display_key(row.key),
                "total": int(row.total),
                "share": int(row.total) / total * 100,
            })
        return result

    @staticmethod
    def _daily_records(df):
        return [
            {"date": str(row.date), "total": int(row.total_keys)}
            for row in df.itertuples()
        ]

    @staticmethod
    def _session_histogram(sessions):
        if sessions.empty:
            return [{"label": label, "total": 0} for label in ["0-15", "15-30", "30-60", "60-90", "90+"]]
        bins = [
            ("0-15", 0, 15),
            ("15-30", 15, 30),
            ("30-60", 30, 60),
            ("60-90", 60, 90),
            ("90+", 90, float("inf")),
        ]
        values = sessions["minutes"].astype(float)
        result = []
        for label, start, end in bins:
            if end == float("inf"):
                count = int((values >= start).sum())
            else:
                count = int(((values >= start) & (values < end)).sum())
            result.append({"label": label, "total": count})
        return result

    def _report_payload(self, fatigue, top_keys):
        hourly = self.stats.hourly_counts()
        sessions = self.stats.session_lengths(30)
        components = fatigue["components"]
        return {
            "summary": self.stats.today_summary(),
            "fatigue": {
                "score": float(fatigue["score"]),
                "level": fatigue["level"],
                "components": [
                    {"label": "今日总量", "value": float(components["total_factor"])},
                    {"label": "近1小时", "value": float(components["recent_intensity_factor"])},
                    {"label": "最长Session", "value": float(components["longest_session_factor"])},
                    {"label": "波动性", "value": float(components["volatility_factor"])},
                ],
            },
            "hourly": [
                {"hour": int(row.hour), "total": int(row.total)}
                for row in hourly.itertuples()
            ],
            "sevenDay": self._daily_records(self.trends.seven_day_trend()),
            "thirtyDay": self._daily_records(self.trends.thirty_day_trend()),
            "sessionHistogram": self._session_histogram(sessions),
            "topKeys": top_keys,
        }

    @staticmethod
    def _guess_activity(top_keys):
        counts = {item["key"]: item["total"] for item in top_keys}
        total_top = max(sum(counts.values()), 1)

        editing_keys = counts.get("Backspace", 0) + counts.get("Delete", 0)
        navigation_keys = sum(counts.get(k, 0) for k in ["Arrow Up", "Arrow Down", "Arrow Left", "Arrow Right", "Tab"])
        text_keys = counts.get("Space", 0) + counts.get("Enter", 0)
        code_symbols = sum(counts.get(k, 0) for k in ["(", ")", "{", "}", "[", "]", ";", ":", "'", '"', ".", ",", "_", "-", "="])

        if not top_keys:
            return "暂无足够数据，无法判断主要活动。"
        if code_symbols / total_top >= 0.18 or counts.get("Tab", 0) / total_top >= 0.12:
            return "高频符号键和 Tab 较多，可能主要在写代码、编辑配置或处理结构化文本。"
        if navigation_keys / total_top >= 0.25:
            return "方向键和 Tab 占比较高，可能主要在表格、表单、文档或代码中进行导航和整理。"
        if editing_keys / total_top >= 0.18:
            return "Backspace/Delete 占比较高，可能处于大量修改、润色、调试或纠错状态。"
        if text_keys / total_top >= 0.22:
            return "Space/Enter 频率较高，可能主要在写作、聊天、记录笔记或撰写文档。"
        return "按键分布较均衡，可能是在混合办公：输入文字、切换位置和少量编辑并行发生。"

    def generate_daily_report(self):
        today = date.today().isoformat()
        summary = self.stats.today_summary()
        fatigue = self.fatigue.calculate()
        anomalies = self.anomalies.detect()
        peaks = self.trends.peak_hours()
        lows = self.trends.low_activity_periods()
        top_keys = self._top_key_summary()
        activity_guess = self._guess_activity(top_keys)
        payload = self._report_payload(fatigue, top_keys)

        chart_path = REPORT_DIR / "report.png"
        fig = make_dashboard_figure(self.stats, self.trends)
        fig.savefig(chart_path, bbox_inches="tight")

        html = render_html(
            summary,
            fatigue,
            anomalies,
            peaks,
            lows,
            top_keys,
            activity_guess,
            chart_path.name,
            payload,
        )
        (REPORT_DIR / "report.html").write_text(html, encoding="utf-8")

        anomaly_lines = "\n".join([f"- {a['type']}: {a['message']}" for a in anomalies]) or "- 暂无异常"
        key_lines = "\n".join(
            [f"- {item['key']}: {item['total']} 次 ({item['share']:.1f}%)" for item in top_keys]
        ) or "- 暂无按键记录"
        summary_text = f"""Keyboard Fitness Daily Summary - {today}
今日总按键: {summary['today_total']}
昨日对比: {summary['delta_vs_yesterday']:+d}
7日均值: {summary['seven_day_mean']:.0f}
Fatigue Score: {fatigue['score']:.1f} ({fatigue['level']})
高峰时段: {", ".join(peaks) or "暂无"}
低效时段: {", ".join(lows) or "暂无"}
按键频率 Top 10:
{key_lines}
可能主要在做: {activity_guess}
异常:
{anomaly_lines}
"""
        (REPORT_DIR / "report_summary.txt").write_text(summary_text, encoding="utf-8")
        return {
            "html": REPORT_DIR / "report.html",
            "png": chart_path,
            "summary": REPORT_DIR / "report_summary.txt",
        }

    def generate_weekly_report(self):
        paths = self.generate_daily_report()
        weekly = self.trends.seven_day_trend()
        weekly.to_csv(REPORT_DIR / "weekly_stats.csv", index=False)
        return paths
