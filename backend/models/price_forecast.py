from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from backend.database.database import Base


class PriceForecast(Base):
    __tablename__ = "price_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    store_product_id = Column(Integer, ForeignKey("store_products.id", ondelete="SET NULL"), nullable=True)
    forecast_date = Column(DateTime, nullable=False)
    predicted_price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, nullable=False)

    product = relationship("Product", back_populates="forecasts")
    store_product = relationship("StoreProduct", back_populates="forecasts")

    __table_args__ = (
        CheckConstraint("predicted_price >= 0", name="check_predicted_price_non_negative"),
    )