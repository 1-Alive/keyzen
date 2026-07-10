from apscheduler.schedulers.background import BackgroundScheduler

from config import DAILY_REPORT_HOUR, DAILY_REPORT_MINUTE, STATS_CACHE_REFRESH_MINUTES


def start_scheduler(db, fatigue_model, report_generator):
    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    def refresh_cache():
        fatigue = fatigue_model.calculate()
        db.update_daily_stats(fatigue_score=fatigue["score"])

    scheduler.add_job(
        report_generator.generate_daily_report,
        "cron",
        hour=DAILY_REPORT_HOUR,
        minute=DAILY_REPORT_MINUTE,
        id="daily_report",
        replace_existing=True,
    )
    scheduler.add_job(
        report_generator.generate_weekly_report,
        "cron",
        day_of_week="sun",
        hour=DAILY_REPORT_HOUR,
        minute=DAILY_REPORT_MINUTE,
        id="weekly_report",
        replace_existing=True,
    )
    scheduler.add_job(
        refresh_cache,
        "interval",
        minutes=STATS_CACHE_REFRESH_MINUTES,
        id="stats_cache",
        replace_existing=True,
    )
    scheduler.start()
    refresh_cache()
    return scheduler

