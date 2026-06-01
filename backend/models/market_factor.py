from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint

from backend.database.database import Base


class MarketFactor(Base):
    __tablename__ = "market_factors"

    id = Column(Integer, primary_key=True, index=True)

    factor_name = Column(String(100), nullable=False)
    factor_type = Column(String(50), nullable=False)

    value = Column(Float, nullable=False)
    measured_at = Column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "factor_name",
            "measured_at",
            name="uq_market_factor_name_date"
        ),
    )