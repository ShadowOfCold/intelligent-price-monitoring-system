from datetime import datetime

from pydantic import BaseModel


class ReportRequest(BaseModel):
    product_id: int


class ReportResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    created_at: datetime
    period_start: datetime
    period_end: datetime

    class Config:
        from_attributes = True