from aiogram.filters.callback_data import CallbackData
from aiogram import Router, types
from app.repos.user import UserRepository
from app.services.db import get_session
from .purchase_history import show_purchase_history


class UserProfileCallback(CallbackData, prefix="user_profile"):
    action: str
    
def get_callbacks_user_router(async_session_maker, ranks) -> Router:
    
    router = Router()
    
    @router.callback_query(UserProfileCallback.filter())
    async def profile_cb(query: types.CallbackQuery, callback_data: UserProfileCallback):
        if callback_data.action == "rank_progress":
            tg = query.from_user
            async with get_session(async_session_maker) as session:
                repo = UserRepository(session)
                user = await repo.get_by_tg_id(tg.id)

                if user is None:
                    user = await repo.create(tg_id=tg.id, username=tg.username)
                else:
                    await session.refresh(user)

                rank_range = await ranks.get_rank_points_range_by_points(user.rank_points)
                next_rank = await ranks.get_rank_by_points(rank_range[1]+1) if rank_range[1] != 0 else None

                if next_rank:
                    await query.answer(f"{rank_range[0]} --- {user.rank_points} --- {rank_range[1]} \nСледующий ранг: {next_rank.name}", show_alert=True)
                else: 
                    await query.answer("У вас максимальный ранг! Поздравляем!")
                
        elif callback_data.action == "purchase_history":
            async with get_session(async_session_maker) as session:
                await show_purchase_history(query, session)
            
        else:
            await query.answer("Неизвестное действие", show_alert=False)
                        
    return router
