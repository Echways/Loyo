# app/factory.py
"""
Application factory: создаёт и конфигурирует Bot, Dispatcher, DB, Redis и сервисы.
(исправлено: использование DefaultBotProperties вместо устаревшего parse_mode)
"""
import asyncio
import aiohttp
from types import SimpleNamespace
from pathlib import Path
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
# new imports for default bot properties
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import ClientTimeout, TCPConnector
from aiogram.client.session.aiohttp import AiohttpSession

from .config import settings
from .services.db import make_engine_and_session
from .services.redis import make_redis
from .services.ranks import RanksStore

log = logging.getLogger(__name__)

async def create_app() -> SimpleNamespace:
    # Create bot with new-style default properties (parse_mode moved out of Bot constructor).
    # This replaces the old: Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
    
    timeout_seconds = 15
    bot_session = AiohttpSession(timeout=ClientTimeout(total=timeout_seconds))
    
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=bot_session,
    )

    dp = Dispatcher(storage=MemoryStorage())

    # DB engine and session maker
    engine, async_session_maker = make_engine_and_session(settings.DB_DSN)


    # Redis (optional)
    redis = None
    try:
        redis = await make_redis(settings.REDIS_DSN)
        log.info("Connected to Redis: %s", settings.REDIS_DSN)
    except Exception as e:
        log.warning("Redis unavailable at startup: %s", e)
        redis = None

    # Ranks store
    ranks = RanksStore(redis=redis)
    ranks_file = Path(settings.RANKS_FILE)
    try:
        await ranks.load_from_file(ranks_file)
        log.info("Loaded ranks from %s", ranks_file)
    except Exception as e:
        log.exception("Failed to load ranks: %s", e)

    # Register handlers (pass admin ids and ranks file so handlers can access them)
    admin_ids = settings.admin_ids()
    try:
        from .handlers import register_handlers
        register_handlers(dp, ranks, async_session_maker, redis=redis, admin_ids=admin_ids, ranks_file=ranks_file)
    except Exception as e:
        log.warning("Could not auto-register handlers: %s", e)
        
    await bot.delete_webhook(drop_pending_updates=True)

    ns = SimpleNamespace(
        bot=bot,
        dp=dp,
        engine=engine,
        async_session_maker=async_session_maker,
        ranks=ranks,
        redis=redis,
        admin_ids=admin_ids,
    )
    return ns
