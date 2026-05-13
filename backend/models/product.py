from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.database.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100))

    store_products = relationship("StoreProduct", back_populates="product", cascade="all, delete-orphan")
    prices = relationship("Price", back_populates="product", cascade="all, delete-orphan")
    forecasts = relationship("PriceForecast", back_populates="product", cascade="all, delete-orphan")
    correlation_results = relationship("CorrelationAnalysisResult", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("name", name="uq_product_name"),
    )