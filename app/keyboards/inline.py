from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.handlers.callbacks_user import UserProfileCallback

user_profile_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Прогресс ранга", callback_data=UserProfileCallback(action="rank_progress").pack()),
            InlineKeyboardButton(text="История покупок", callback_data=UserProfileCallback(action="purchase_history").pack()),
        ],
        [
            InlineKeyboardButton(text="Помощь", url="https://t.me/your_support_bot"),
        ],
    ]
)
