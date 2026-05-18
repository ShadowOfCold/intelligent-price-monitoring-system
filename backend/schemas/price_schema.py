from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PriceCreate(BaseModel):
    product_id: int
    store_product_id: int | None = None
    document_id: int | None = None
    price: Decimal
    checked_at: datetime


class PriceResponse(BaseModel):
    id: int
    product_id: int
    store_product_id: int | None
    document_id: int | None
    price: Decimal
    checked_at: datetime

    class Config:
        from_attributes = True