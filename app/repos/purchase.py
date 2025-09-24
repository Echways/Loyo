from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.purchase import Pending, PurchaseHistory


class PendingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, record: Dict[str, Any]) -> Pending:
        inst = Pending(**record)
        self.session.add(inst)
        await self.session.flush()
        await self.session.commit()
        return inst

    async def get(self, purchase_id: str) -> Optional[Pending]:
        q = select(Pending).where(Pending.purchase_id == purchase_id)
        r = await self.session.execute(q)
        inst: Optional[Pending] = r.scalar_one_or_none()
        return inst

    async def mark_confirmed(self, purchase_id: str, confirmed_by: int, awarded_points: int) -> bool:
        inst = await self.get(purchase_id)
        if not inst:
            return False
        inst.status = "confirmed"
        inst.confirmed_by = confirmed_by
        inst.awarded_points = awarded_points
        inst.confirmed_at = datetime.now()
        self.session.add(inst)
        await self.session.commit()
        return True


class PurchaseHistoryRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_if_present(self, payload: Dict[str, Any]) -> Optional[PurchaseHistory]:
        allowed = {c.name for c in PurchaseHistory.__table__.columns}
        filtered = {k: v for k, v in payload.items() if k in allowed}
        if not filtered:
            return None
        inst = PurchaseHistory(**filtered)
        self.session.add(inst)
        await self.session.commit()
        return inst

    async def update_if_present(self, purchase_id: str, updates: Dict[str, Any]) -> bool:
        allowed = {c.name for c in PurchaseHistory.__table__.columns}
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return False
        q = select(PurchaseHistory).where(PurchaseHistory.purchase_id == purchase_id)
        r = await self.session.execute(q)
        inst: Optional[PurchaseHistory] = r.scalar_one_or_none()
        if not inst:
            return False
        for k, v in filtered.items():
            setattr(inst, k, v)
        self.session.add(inst)
        await self.session.commit()
        return True
