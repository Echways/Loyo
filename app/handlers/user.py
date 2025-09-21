# app/handlers/user.py
from aiogram import Router, types
from aiogram.filters import Command
from aiogram import F
from app.services.db import get_session
from app.repos.user import UserRepository
from app.keyboards.reply import index_reply_kb
from app.keyboards.inline import user_profile_keyboard
from typing import Any

def get_user_router(async_session_maker, ranks) -> Router:
    router = Router()
    
    @router.message(Command("start"))
    async def cmd_start(message: types.Message):
        await message.answer("Добро пожаловать! Воспользуйся клавиатурой ниже для доступа к возможностям.", reply_markup=index_reply_kb)

    @router.message(F.text == '👤 Мой профиль')
    async def cmd_profile(message: types.Message):
        tg = message.from_user
        async with get_session(async_session_maker) as session:
            repo = UserRepository(session)
            user = await repo.get_by_tg_id(tg.id)
            if not user:
                user = await repo.create(tg_id=tg.id, username=tg.username)

            rank_item = await ranks.get_rank_by_points(user.rank_points)
            rank_name = rank_item.name if rank_item else "—"
            cashback_percent = rank_item.cashback_percent if rank_item else 0

            await message.answer(
                f"Профиль:\nID: {user.tg_id}\nНик: @{user.username or '-'}\nОчки: {user.bonus_points}\nРанг: {rank_name}\nКэшбек: {cashback_percent}%",
                reply_markup=user_profile_keyboard
            )

    # @router.message()
    # async def cmd_rank(message: types.Message):
    #     tg = message.from_user
    #     async with get_session(async_session_maker) as session:
    #         repo = UserRepository(session)
    #         user = await repo.get_by_tg_id(tg.id)
    #         if not user:
    #             await message.answer("Вы ещё не зарегистрированы. Сначала /start или /profile.")
    #             return router
    #         rank = await ranks.get_rank_by_points(user.points)
    #         await message.answer(f"У вас {user.points} очков. Ранг: {rank.name if rank else '—'}")

    return router
