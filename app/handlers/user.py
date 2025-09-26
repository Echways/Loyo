from aiogram import Router, types
from aiogram.filters import Command
from aiogram import F
from app.services.db import get_session
from app.repos.user import UserRepository
from app.keyboards.reply import index_reply_kb
from app.keyboards.inline import user_profile_keyboard
from app.services.catalog import CatalogService
from app.keyboards.catalog import build_catalog_markup


def get_user_router(async_session_maker, ranks, admin_ids, catalog_file) -> Router:
    router = Router()

    @router.message(Command("start"))
    async def cmd_start(message: types.Message):
        await message.answer(
            "Добро пожаловать! Воспользуйся клавиатурой ниже для доступа к возможностям.",
            reply_markup=index_reply_kb,
        )

    @router.message(F.text == "👤 Мой профиль")
    async def cmd_profile(message: types.Message):
        tg = message.from_user
        async with get_session(async_session_maker) as session:
            repo = UserRepository(session)
            user = await repo.get_by_tg_id(tg.id)
            if not user:
                user = await repo.create(tg_id=tg.id, username=tg.username)

            rank_item = await ranks.get_rank_by_points(user.rank_points)
            rank_name = rank_item.name
            cashback_percent = rank_item.cashback_percent

            await message.answer(
                f"Профиль:\nID: {user.tg_id}\nБонусные очки: {user.bonus_points}\nРанг: {rank_name}\nКэшбек: {cashback_percent}%",
                reply_markup=user_profile_keyboard,
            )

    @router.message(F.text == "👀 Список товаров")
    async def show_catalog(message: types.Message):
        service = CatalogService(admin_ids=admin_ids)
        catalog = await service.load_from_file(catalog_file)
        markup = await build_catalog_markup(catalog, include_back=False)
        await message.answer(
            text=f"📚 <b>{catalog.get('title')}</b>\nВыберите категорию или товар:",
            reply_markup=markup,
        )

    return router
