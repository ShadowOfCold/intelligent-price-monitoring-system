from pydantic import BaseModel


class StoreCreate(BaseModel):
    name: str
    base_url: str


class StoreResponse(BaseModel):
    id: int
    name: str
    base_url: str

    class Config:
        from_attributes = True