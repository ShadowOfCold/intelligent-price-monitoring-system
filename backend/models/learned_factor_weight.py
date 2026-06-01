from sqlalchemy import Column, DateTime, Float, Integer, String, CheckConstraint

from backend.database.database import Base


class LearnedFactorWeight(Base):
    __tablename__ = "learned_factor_weights"

    id = Column(Integer, primary_key=True, index=True)

    category = Column(String(100), nullable=False)
    factor_name = Column(String(100), nullable=False)

    importance = Column(Float, nullable=False)
    sample_size = Column(Integer, nullable=False)

    calculated_at = Column(DateTime, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "importance >= 0 AND importance <= 1",
            name="check_learned_factor_importance_range"
        ),
        CheckConstraint(
            "sample_size >= 0",
            name="check_learned_factor_sample_size"
        ),
    )