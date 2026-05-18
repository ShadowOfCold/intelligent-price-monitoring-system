from pydantic import BaseModel, Field


class SchedulerRunRequest(BaseModel):
    collect_prices: bool = True
    detect_anomalies: bool = True
    analyze_correlations: bool = True
    generate_forecasts: bool = True
    generate_reports: bool = True
    forecast_days_count: int = 7
    report_format: str = "both"


class SchedulerConfigRequest(BaseModel):
    enabled: bool = False
    run_times: list[str] = Field(default_factory=lambda: ["09:00"])

    collect_prices: bool = True
    detect_anomalies: bool = True
    analyze_correlations: bool = True
    generate_forecasts: bool = True
    generate_reports: bool = True

    forecast_days_count: int = 7
    report_format: str = "both"