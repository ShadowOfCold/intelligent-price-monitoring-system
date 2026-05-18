from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from backend.database.database import Base


class DetectedAnomaly(Base):
    __tablename__ = "detected_anomalies"

    id = Column(Integer, primary_key=True, index=True)
    price_id = Column(Integer, ForeignKey("prices.id", ondelete="CASCADE"), nullable=False)
    anomaly_type = Column(String(100), nullable=False)
    anomaly_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    detected_at = Column(DateTime, nullable=False)

    price = relationship("Price", back_populates="anomalies")

    __table_args__ = (
        CheckConstraint("risk_level IN ('low', 'medium', 'high')", name="check_anomaly_risk_level"),
    )