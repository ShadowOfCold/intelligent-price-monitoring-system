from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class DetectedAnomalyResponse(BaseModel):
    id: int
    price_id: int
    anomaly_type: str
    anomaly_score: float
    risk_level: str
    detected_at: datetime

    class Config:
        from_attributes = True


class AnomalyWithPriceResponse(BaseModel):
    id: int
    price_id: int
    product_id: int
    price: Decimal
    checked_at: datetime
    anomaly_type: str
    anomaly_score: float
    risk_level: str
    detected_at: datetime