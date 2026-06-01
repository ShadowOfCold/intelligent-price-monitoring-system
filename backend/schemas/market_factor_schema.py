from datetime import datetime

from pydantic import BaseModel, Field


class MarketFactorCreate(BaseModel):
    factor_name: str
    factor_type: str
    value: float
    measured_at: datetime


class MarketFactorResponse(BaseModel):
    id: int
    factor_name: str
    factor_type: str
    value: float
    measured_at: datetime

    class Config:
        from_attributes = True


class CategoryFactorWeightCreate(BaseModel):
    category: str
    factor_name: str
    weight: float = Field(ge=0, le=1)


class CategoryFactorWeightResponse(BaseModel):
    id: int
    category: str
    factor_name: str
    weight: float

    class Config:
        from_attributes = True