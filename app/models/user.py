from sqlalchemy import Column, BigInteger, Integer, String, DateTime, func
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(64), nullable=True)
    bonus_points = Column(Integer, default=0, nullable=False)
    rank_points = Column(Integer, default=0, nullable=False)
    rank = Column(String(64), nullable=True)
    cashback_percent = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<User id={self.id} tg_id={self.tg_id} points={self.bonus_points}>"
