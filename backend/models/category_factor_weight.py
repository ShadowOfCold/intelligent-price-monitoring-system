from sqlalchemy import Column, Integer, String, Float, UniqueConstraint, CheckConstraint

from backend.database.database import Base


class CategoryFactorWeight(Base):
    __tablename__ = "category_factor_weights"

    id = Column(Integer, primary_key=True, index=True)

    category = Column(String(100), nullable=False)
    factor_name = Column(String(100), nullable=False)
    weight = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "category",
            "factor_name",
            name="uq_category_factor"
        ),
        CheckConstraint(
            "weight >= 0 AND weight <= 1",
            name="check_factor_weight_range"
        ),
    )