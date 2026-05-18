from datetime import datetime

from pydantic import BaseModel


class CorrelationAnalysisResponse(BaseModel):
    id: int
    product_id: int
    first_store_product_id: int
    second_store_product_id: int
    correlation_value: float
    period_start: datetime
    period_end: datetime
    risk_level: str
    created_at: datetime

    class Config:
        from_attributes = True


class CorrelationAnalysisWithStoresResponse(BaseModel):
    id: int
    product_id: int
    first_store_product_id: int
    second_store_product_id: int
    first_store_name: str
    second_store_name: str
    correlation_value: float
    period_start: datetime
    period_end: datetime
    risk_level: str
    created_at: datetime