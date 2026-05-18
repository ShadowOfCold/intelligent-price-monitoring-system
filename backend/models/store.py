from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database.database import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    base_url = Column(Text, nullable=False)

    store_products = relationship("StoreProduct", back_populates="store", cascade="all, delete-orphan")