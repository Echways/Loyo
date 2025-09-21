# Простая точка входа для разработки: создаёт app, стартует polling, корректно закрывает ресурсы.
import asyncio
from pathlib import Path
from app.factory import create_app
from app.services.redis import close_redis
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    app = await create_app()
    bot = app.bot
    dp = app.dp

    print("Starting polling...")
    try:
        # Start polling; aiogram will run handlers registered in factory
        await dp.start_polling(bot)
    finally:
        # Graceful shutdown
        try:
            await bot.session.close()
        except Exception:
            pass
        try:
            await app.engine.dispose()
        except Exception:
            pass
        try:
            await close_redis()
        except Exception:
            pass
        print("Shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())
