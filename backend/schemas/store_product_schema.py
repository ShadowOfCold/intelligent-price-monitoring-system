from pydantic import BaseModel


class StoreProductCreate(BaseModel):
    product_id: int
    store_id: int
    product_url: str


class StoreProductResponse(BaseModel):
    id: int
    product_id: int
    store_id: int
    product_url: str

    class Config:
        from_attributes = True