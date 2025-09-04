import asyncio
import logging
from aiogram.types.bot_command import BotCommand

from app import create_bot_and_dispatcher
from app.config import settings

logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    bot, dp, redis_client = await create_bot_and_dispatcher()

    # (опционально) init db (только при dev, в продакшне используйте alembic)
    # await init_db()

    # Зарегистрируйте роутеры: import и dp.include_router(...)
    # Пример: from app.handlers import router; dp.include_router(router)

    # Рекомендуется перед запуском установить команды бота
    await bot.set_my_commands([
        BotCommand(command="start", description="Start bot"),
    ])

    try:
        # skip_updates=True — не обрабатывать старые апдейты
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()
        if redis_client:
            await redis_client.close()

if __name__ == "__main__":
    asyncio.run(main())
