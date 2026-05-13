from sqlalchemy import Column, Integer, String, Text, DateTime, CheckConstraint

from backend.database.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    __table_args__ = (
        CheckConstraint("period_start <= period_end", name="check_report_period"),
    )