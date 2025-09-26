from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.services.ranks import RanksStore


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.ranks = RanksStore()

    async def get_by_tg_id(self, tg_id: int) -> Optional[User]:
        res = await self.session.execute(select(User).where(User.tg_id == tg_id))
        return res.scalars().first()

    async def create(self, tg_id: int, username: Optional[str] = None) -> User:
        user = User(tg_id=tg_id, username=username)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def add_rank_points(self, tg_id: int, delta: int) -> User:
        result = await self.session.execute(
            select(User).where(User.tg_id == tg_id).with_for_update()
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"User with tg_id={tg_id} not found")

        user.rank_points = (user.rank_points or 0) + delta

        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def add_bonus_points(self, tg_id: int, delta: int) -> User:
        result = await self.session.execute(
            select(User).where(User.tg_id == tg_id).with_for_update()
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"User with tg_id={tg_id} not found")

        user.bonus_points = (user.bonus_points or 0) + delta

        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def redeem_bonus_points(self, tg_id: int, delta: int) -> User:
        result = await self.session.execute(
            select(User).where(User.tg_id == tg_id).with_for_update()
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"User with tg_id={tg_id} not found")

        user.bonus_points = (user.bonus_points or 0) - delta

        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def set_rank(self, tg_id: int, rank_name: str) -> User:
        result = await self.session.execute(
            select(User).where(User.tg_id == tg_id).with_for_update()
        )

        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"User with tg_id={tg_id} not found")
        user.rank = rank_name

        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def list_all(self) -> List[User]:
        res = await self.session.execute(select(User))
        return res.scalars().all()
