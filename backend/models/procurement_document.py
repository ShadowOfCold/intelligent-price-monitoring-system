from sqlalchemy import Column, Integer, String, Text, DateTime, CheckConstraint
from sqlalchemy.orm import relationship

from backend.database.database import Base


class ProcurementDocument(Base):
    __tablename__ = "procurement_documents"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_path = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, nullable=False)

    prices = relationship("Price", back_populates="document")

    __table_args__ = (
        CheckConstraint("file_type IN ('PDF', 'XLSX')", name="check_file_type"),
    )