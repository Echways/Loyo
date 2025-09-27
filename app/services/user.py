from app.repos.user import UserRepository
from app.services.db import get_session


async def get_user_bonus(async_session_maker, user_id):
    user_bonus = 0
    try:
        async with get_session(async_session_maker) as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_tg_id(user_id)
            user_bonus = (
                int(user.bonus_points)
                if user and getattr(user, "bonus_points", None) is not None
                else 0
            )
            return user_bonus
    except Exception:
        user_bonus = 0
        return user_bonus
