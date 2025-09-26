from aiogram.filters.callback_data import CallbackData
from aiogram import Router, types


class MenuCallback(CallbackData, prefix="admin"):
    action: str


def get_callbacks_router(async_session_maker) -> Router:
    router = Router()

    return router
