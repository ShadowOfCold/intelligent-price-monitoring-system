from pydantic import BaseModel


class PriceDeleteMultipleRequest(BaseModel):
    price_ids: list[int]