from sqlalchemy import Column, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.database.database import Base


class StoreProduct(Base):
    __tablename__ = "store_products"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    product_url = Column(Text, nullable=False)

    product = relationship("Product", back_populates="store_products")
    store = relationship("Store", back_populates="store_products")
    prices = relationship("Price", back_populates="store_product", cascade="all, delete-orphan")
    forecasts = relationship("PriceForecast", back_populates="store_product", cascade="all, delete-orphan")
    correlation_results_as_first = relationship("CorrelationAnalysisResult", foreign_keys="CorrelationAnalysisResult.first_store_product_id", cascade="all, delete-orphan")
    correlation_results_as_second = relationship("CorrelationAnalysisResult", foreign_keys="CorrelationAnalysisResult.second_store_product_id", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("product_id", "store_id", name="uq_product_store"),
    )