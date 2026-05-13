from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from backend.database.database import Base


class Price(Base):
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    store_product_id = Column(Integer, ForeignKey("store_products.id", ondelete="SET NULL"), nullable=True)
    document_id = Column(Integer, ForeignKey("procurement_documents.id", ondelete="SET NULL"), nullable=True)
    price = Column(Numeric(12, 2), nullable=False)
    checked_at = Column(DateTime, nullable=False)

    product = relationship("Product", back_populates="prices")
    store_product = relationship("StoreProduct", back_populates="prices")
    document = relationship("ProcurementDocument", back_populates="prices")
    anomalies = relationship("DetectedAnomaly", back_populates="price", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("price >= 0", name="check_price_non_negative"),
        CheckConstraint(
            "(store_product_id IS NOT NULL AND document_id IS NULL) OR "
            "(store_product_id IS NULL AND document_id IS NOT NULL)",
            name="check_price_source"
        ),
    )