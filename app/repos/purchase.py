from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.purchase import Pending, PurchaseHistory


class PendingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, record: Dict[str, Any]) -> Pending:
        inst = Pending(**record)
        self.session.add(inst)
        await self.session.commit()
        await self.session.refresh(inst)
        return inst

    async def get(self, purchase_id: str) -> Optional[Pending]:
        result = await self.session.execute(
            select(Pending).where(Pending.purchase_id == purchase_id)
        )
        return result.scalar_one_or_none()

    async def mark_confirmed(
        self, purchase_id: str, confirmed_by: int, awarded_points: int
    ) -> bool:
        result = await self.session.execute(
            select(Pending).where(Pending.purchase_id == purchase_id).with_for_update()
        )
        inst: Optional[Pending] = result.scalar_one_or_none()
        if not inst:
            return False

        inst.status = "confirmed"
        inst.confirmed_by = confirmed_by
        inst.awarded_points = awarded_points
        inst.confirmed_at = datetime.now()

        await self.session.commit()
        await self.session.refresh(inst)
        return True


class PurchaseHistoryRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_if_present(
        self, payload: Dict[str, Any]
    ) -> Optional[PurchaseHistory]:
        allowed = {c.name for c in PurchaseHistory.__table__.columns}
        filtered = {k: v for k, v in payload.items() if k in allowed}

        if not filtered:
            return None

        inst = PurchaseHistory(**filtered)
        self.session.add(inst)
        await self.session.commit()
        await self.session.refresh(inst)  # актуализируем объект после commit

        return inst

    async def update_if_present(
        self, purchase_id: str, updates: Dict[str, Any]
    ) -> bool:
        allowed = {c.name for c in PurchaseHistory.__table__.columns}
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return False

        result = await self.session.execute(
            select(PurchaseHistory)
            .where(PurchaseHistory.purchase_id == purchase_id)
            .with_for_update()
        )

        inst: Optional[PurchaseHistory] = result.scalar_one_or_none()
        if inst is None:
            return False

        for k, v in filtered.items():
            setattr(inst, k, v)

        await self.session.commit()
        await self.session.refresh(inst)

        return True

    async def get_history_by_tg_id(
        self, tg_id: int, limit: int
    ) -> list[PurchaseHistory]:
        res = await self.session.execute(
            select(PurchaseHistory)
            .where(PurchaseHistory.user_id == tg_id)
            .where(PurchaseHistory.status == "confirmed")
            .order_by(desc(PurchaseHistory.created_at))
            .limit(limit)
        )
        return res.scalars().all()
