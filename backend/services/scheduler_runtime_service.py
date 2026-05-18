import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.database.database import SessionLocal
from backend.services.scheduler_service import run_full_monitoring_cycle


CONFIG_PATH = "data/scheduler_config.json"

scheduler = BackgroundScheduler(
    timezone="Asia/Irkutsk",
    job_defaults={
        "misfire_grace_time": 300,
        "coalesce": True,
        "max_instances": 1
    }
)

DEFAULT_CONFIG = {
    "enabled": False,
    "run_times": ["09:00"],
    "collect_prices": True,
    "detect_anomalies": True,
    "analyze_correlations": True,
    "generate_forecasts": True,
    "generate_reports": True,
    "forecast_days_count": 7,
    "report_format": "both",
    "last_run_at": None,
    "last_result": None,
}


def ensure_config_directory():
    os.makedirs("data", exist_ok=True)


def load_scheduler_config() -> dict:
    ensure_config_directory()

    if not os.path.exists(CONFIG_PATH):
        save_scheduler_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = json.load(file)

    result = DEFAULT_CONFIG.copy()
    result.update(config)

    return result


def save_scheduler_config(config: dict) -> dict:
    ensure_config_directory()

    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        json.dump(
            config,
            file,
            ensure_ascii=False,
            indent=4
        )

    return config


def run_scheduled_monitoring_cycle():
    config = load_scheduler_config()

    db = SessionLocal()

    try:
        result = run_full_monitoring_cycle(
            db=db,
            collect_prices=config["collect_prices"],
            detect_anomalies=config["detect_anomalies"],
            analyze_correlations=config["analyze_correlations"],
            generate_forecasts=config["generate_forecasts"],
            generate_reports=config["generate_reports"],
            forecast_days_count=config["forecast_days_count"],
            report_format=config["report_format"],
        )

        config["last_run_at"] = datetime.now(
            ZoneInfo("Asia/Irkutsk")
        ).isoformat()
        config["last_result"] = result

        save_scheduler_config(config)

    finally:
        db.close()


def clear_scheduler_jobs():
    for job in scheduler.get_jobs():
        scheduler.remove_job(job.id)


def apply_scheduler_config():
    config = load_scheduler_config()

    clear_scheduler_jobs()

    if not config["enabled"]:
        return config

    for index, run_time in enumerate(config["run_times"]):
        hour, minute = run_time.split(":")

        scheduler.add_job(
            run_scheduled_monitoring_cycle,
            trigger=CronTrigger(
                hour=int(hour),
                minute=int(minute),
                timezone="Asia/Irkutsk"
            ),
            id=f"monitoring_cycle_{index}",
            replace_existing=True,
            misfire_grace_time=300,
            coalesce=True,
            max_instances=1
        )

    return config


def update_scheduler_config(new_config: dict) -> dict:
    config = load_scheduler_config()

    config.update(new_config)

    save_scheduler_config(config)
    apply_scheduler_config()

    return config


def start_scheduler():
    apply_scheduler_config()

    if not scheduler.running:
        scheduler.start()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()