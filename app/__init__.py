import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage  # aiogram предоставляет Redis-сторедж
import redis.asyncio as aioredis  # redis-py с asyncio API

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

logger = logging.getLogger(__name__)

# --- Бот и диспетчер (не создаём глобально, а через фабрику) ---
async def create_bot_and_dispatcher():
    default=DefaultBotPro
    bot = bot(token=settings.BOT_TOKEN)
    # Storage: Memory для разработки, Redis для продакшн (если задан REDIS_URL)
    redis_client = None
    if settings.REDIS_URL:
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        storage = RedisStorage(redis=redis_client)  # aiogram Redis storage
    else:
        storage = MemoryStorage()

    dp = Dispatcher(storage=storage)
    # можно зарегистрировать глобальные middlewares/роутеры здесь или в main
    return bot, dp, redis_client

# --- SQLAlchemy async setup ---

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

database_url = str(settings.DATABASE_URL)  # <- важное приведение в str
engine = create_async_engine(database_url, echo=settings.DEBUG, future=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
