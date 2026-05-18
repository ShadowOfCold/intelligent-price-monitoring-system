from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from backend.database.database import Base


class CorrelationAnalysisResult(Base):
    __tablename__ = "correlation_analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    first_store_product_id = Column(Integer, ForeignKey("store_products.id", ondelete="CASCADE"), nullable=False)
    second_store_product_id = Column(Integer, ForeignKey("store_products.id", ondelete="CASCADE"), nullable=False)
    correlation_value = Column(Float, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    risk_level = Column(String(20), nullable=False)
    created_at = Column(DateTime, nullable=False)

    product = relationship("Product", back_populates="correlation_results")

    __table_args__ = (
        CheckConstraint("correlation_value >= -1 AND correlation_value <= 1", name="check_correlation_value"),
        CheckConstraint("first_store_product_id <> second_store_product_id", name="check_different_store_products"),
        CheckConstraint("period_start <= period_end", name="check_correlation_period"),
        CheckConstraint("risk_level IN ('low', 'medium', 'high')", name="check_correlation_risk_level"),
    )