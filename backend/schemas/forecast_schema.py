from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ForecastCreateRequest(BaseModel):
    store_product_id: int
    days_count: int = 7


class PriceForecastResponse(BaseModel):
    id: int
    product_id: int
    store_product_id: int | None
    forecast_date: datetime
    predicted_price: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class ForecastMetricsResponse(BaseModel):
    mae: float
    rmse: float
    mape: float


class ForecastGenerateResponse(BaseModel):
    forecasts: list[PriceForecastResponse]
    metrics: ForecastMetricsResponse