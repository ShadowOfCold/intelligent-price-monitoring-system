from pydantic import BaseModel


class PriceCollectionRequest(BaseModel):
    store_product_id: int