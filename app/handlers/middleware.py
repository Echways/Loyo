# app/handlers/middleware.py
import logging
import asyncio
from aiogram import BaseMiddleware

log = logging.getLogger(__name__)

class ErrorMiddleware(BaseMiddleware):
    def __init__(self, admin_ids=None, redis=None):
        super().__init__()
        self.admin_ids = admin_ids or []
        self.redis = redis

    async def _notify_admins(self, bot, text):
        async def _send(admin_id):
            try:
                # даём короткий таймаут на отправку, чтобы таска не висела вечно
                await asyncio.wait_for(bot.send_message(admin_id, text), timeout=3.0)
            except Exception:
                log.exception("Failed to notify admin %s", admin_id)

        for admin in self.admin_ids:
            # запустим каждую отправку как отдельную фоновую таску
            asyncio.create_task(_send(admin))

    async def __call__(self, handler, event, data):
        try:
            return await handler(event, data)
        except Exception as e:
            log.exception("Unhandled exception in handler")
            bot = data.get("bot")
            if bot and self.admin_ids:
                text = f"⚠️ Ошибка в боте: {e.__class__.__name__}: {e}"
                # уведомление в фоне (не ждём)
                asyncio.create_task(self._notify_admins(bot, text))
            # можно re-raise, если хотите, чтобы aiogram делал дальнейшую обработку:
            # raise
            return
