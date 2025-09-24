import asyncio
import logging
from typing import Optional
import aioredis

log = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None
_redis_lock = asyncio.Lock()

async def make_redis(dsn: str, *, max_connections: int = 10) -> aioredis.Redis:
    global _redis
    async with _redis_lock:
        if _redis is not None:
            return _redis
        try:
            _redis = aioredis.from_url(
                dsn,
                encoding="utf-8",
                decode_responses=True,
                max_connections=max_connections
            )

            try:
                pong = await _redis.ping()
                log.info("Redis connected, PING -> %s", pong)
            except Exception as e:
                await _redis.close()
                _redis = None
                raise
            return _redis
        except Exception as e:
            log.exception("Failed to create Redis client for %s: %s", dsn, e)
            raise

async def close_redis():
    global _redis
    async with _redis_lock:
        if _redis is not None:
            try:
                await _redis.close()
            except Exception:
                log.exception("Error while closing redis")
            finally:
                _redis = None
