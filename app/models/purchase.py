# app/models/purchase.py
from __future__ import annotations
from datetime import datetime
from .base import Base
from sqlalchemy import Column, String, BigInteger, Integer, Text, DateTime, JSON


class Pending(Base):
    __tablename__ = "pending"

    purchase_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    product_id = Column(String(128), nullable=True)
    product_title = Column(Text, nullable=True)
    price = Column(Integer, nullable=True)
    status = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_by = Column(BigInteger, nullable=True)
    awarded_points = Column(Integer, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    payload = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Pending {self.purchase_id} user={self.user_id} product={self.product_id} status={self.status}>"


class PurchaseHistory(Base):
    __tablename__ = "purchase_history"

    purchase_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=True, index=True)
    product_id = Column(String(128), nullable=True)
    product_title = Column(Text, nullable=True)
    price = Column(Integer, nullable=True)
    status = Column(String(32), nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    confirmed_by = Column(BigInteger, nullable=True)
    awarded_points = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"Товар: {self.product_title} Цена: {self.price} Начислено очков: {self.awarded_points} Статус: {self.status}"
