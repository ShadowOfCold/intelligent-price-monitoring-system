from datetime import datetime

from pydantic import BaseModel


class ProcurementDocumentResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True