from types import SimpleNamespace
from pathlib import Path
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import settings
from .services.db import make_engine_and_session
from .services.redis import make_redis
from .services.ranks import RanksStore
from .services.catalog import CatalogService

log = logging.getLogger(__name__)


async def create_app() -> SimpleNamespace:
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())
    engine, async_session_maker = make_engine_and_session(settings.DB_DSN)

    redis = None
    try:
        redis = await make_redis(settings.REDIS_DSN)
        log.info("Connected to Redis: %s", settings.REDIS_DSN)
    except Exception as e:
        log.warning("Redis unavailable at startup: %s", e)
        redis = None

    ranks = RanksStore(redis=redis)
    ranks_file = Path(settings.RANKS_FILE)
    try:
        await ranks.load_from_file(ranks_file)
        log.info("Loaded ranks from %s", ranks_file)
    except Exception as e:
        log.exception("Failed to load ranks: %s", e)

    admin_ids = settings.admin_ids()

    catalog_file = Path(settings.CATALOG_FILE)
    catalog = CatalogService(admin_ids=admin_ids, catalog_file=catalog_file)
    try:
        await catalog.load_from_file(catalog_file)
        log.info("Loaded catalog from %s", catalog_file)
    except Exception as e:
        log.exception("Failed to load catalog: %s", e)

    try:
        from .handlers import register_handlers

        register_handlers(
            dp,
            ranks,
            async_session_maker,
            redis=redis,
            admin_ids=admin_ids,
            ranks_file=ranks_file,
            engine=engine,
            catalog=catalog,
            catalog_file=catalog_file,
        )
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
        catalog=catalog,
    )
    return ns
