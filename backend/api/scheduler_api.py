from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.schemas.scheduler_schema import (
    SchedulerConfigRequest,
    SchedulerRunRequest,
)
from backend.services.scheduler_runtime_service import (
    load_scheduler_config,
    update_scheduler_config,
)
from backend.services.scheduler_service import run_full_monitoring_cycle


router = APIRouter(
    prefix="/scheduler",
    tags=["Автоматизация"]
)


@router.post("/run-full-cycle")
def run_scheduler_cycle(
    data: SchedulerRunRequest,
    db: Session = Depends(get_db)
):
    result = run_full_monitoring_cycle(
        db=db,
        collect_prices=data.collect_prices,
        detect_anomalies=data.detect_anomalies,
        analyze_correlations=data.analyze_correlations,
        generate_forecasts=data.generate_forecasts,
        generate_reports=data.generate_reports,
        forecast_days_count=data.forecast_days_count,
        report_format=data.report_format
    )

    return {
        "message": "Цикл мониторинга выполнен",
        "result": result
    }


@router.get("/config")
def get_scheduler_config():
    return load_scheduler_config()


@router.post("/config")
def save_scheduler_settings(
    data: SchedulerConfigRequest
):
    config = update_scheduler_config(
        data.model_dump()
    )

    return {
        "message": "Настройки расписания сохранены",
        "config": config
    }