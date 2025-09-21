# app/handlers/filters.py
from aiogram.filters import BaseFilter
from aiogram import types
from typing import Iterable

class AdminFilter(BaseFilter):
    def __init__(self, admin_ids: Iterable[int]):
        self.admin_ids = set(admin_ids or [])

    async def __call__(self, message: types.Message) -> bool:
        user = message.from_user
        if not user:
            return False
        return user.id in self.admin_ids
