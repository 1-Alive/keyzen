import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analytics.anomaly_detection import AnomalyDetector
from analytics.fatigue_model import FatigueModel
from analytics.stats import StatsService
from analytics.trends import TrendAnalyzer
from core.db import Database
from core.listener import KeyboardListener
from core.session import SessionManager
from gui.dashboard import Dashboard
from reporting.report_generator import ReportGenerator
from scheduler.jobs import start_scheduler


def build_app():
    db = Database()
    session_manager = SessionManager(db)
    stats = StatsService(db)
    fatigue = FatigueModel(stats)
    anomalies = AnomalyDetector(stats)
    trends = TrendAnalyzer(stats)
    reports = ReportGenerator(stats, fatigue, anomalies, trends)
    listener = KeyboardListener(db, session_manager)
    scheduler = start_scheduler(db, fatigue, reports)
    return db, session_manager, stats, fatigue, anomalies, trends, reports, listener, scheduler


def main():
    _, session_manager, stats, fatigue, anomalies, trends, _, listener, scheduler = build_app()
    try:
        listener.start()
    except RuntimeError as exc:
        print(exc)
    app = Dashboard(stats, fatigue, anomalies, trends, session_manager)
    try:
        app.mainloop()
    finally:
        listener.stop()
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()

