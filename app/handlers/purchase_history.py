from aiogram import types
from app.repos.user import UserRepository
from app.repos.purchase import PurchaseHistoryRepo
from app.services.purchase_history import build_history_text


async def show_purchase_history(query: types.CallbackQuery, session):
    tg = query.from_user

    repo_user = UserRepository(session)
    repo_ph = PurchaseHistoryRepo(session)

    user = await repo_user.get_by_tg_id(tg.id)
    if user is None:
        user = await repo_user.create(tg_id=tg.id, username=tg.username)
    else:
        await session.refresh(user)

    purchases = await repo_ph.get_history_by_tg_id(tg.id, limit=10)

    if not purchases:
        await query.answer("Вы ещё ничего не покупали", show_alert=True)
        return

    text = await build_history_text(purchases)

    try:
        await query.message.edit_text(text)
        await query.answer()
    except Exception:
        await query.message.answer(text)
        await query.answer()
