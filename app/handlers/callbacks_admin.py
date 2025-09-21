from aiogram.filters.callback_data import CallbackData
from aiogram import Router, types

class MenuCallback(CallbackData, prefix="admin"):
    action: str  # просто действие, напр. "profile", "bonuses"

# Создание inline-кнопок
# kb = InlineKeyboardMarkup(inline_keyboard=[
#     [InlineKeyboardButton(text="Профиль", callback_data=MenuCallback(action="profile").pack())],
#     [InlineKeyboardButton(text="Бонусы", callback_data=MenuCallback(action="bonuses").pack())],
# ])


def get_callbacks_router(async_session_maker) -> Router:
    
    router = Router()
    
    @router.callback_query(MenuCallback.filter())
    async def menu_cb(query: types.CallbackQuery, callback_data: MenuCallback):
        # callback_data.action уже разобран и типизирован
        if callback_data.action == "profile":
            await query.message.answer("Открываю профиль...")
        elif callback_data.action == "bonuses":
            await query.message.answer("Показываю бонусы...")
        else:
            await query.answer("Неизвестное действие", show_alert=False)
            
    return router
