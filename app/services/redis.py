try:
    from redis import asyncio as redis_asyncio  # type: ignore

    _BACKEND = "redis"
except Exception:
    redis_asyncio = None  # type: ignore
    _BACKEND = None

if _BACKEND is None:
    try:
        import aioredis  # type: ignore

        _BACKEND = "aioredis"
    except Exception:
        aioredis = None  # type: ignore

if _BACKEND is None:
    raise RuntimeError(
        "Нет установленного async Redis-клиента. Установите пакет 'redis' (redis-py >=4.x): "
        "pip install 'redis>=4.2.0' или добавьте зависимость в pyproject.toml."
    )


async def make_redis(dsn: str, *, decode_responses: bool = True, **kwargs):
    if _BACKEND == "redis":
        client = redis_asyncio.from_url(
            dsn, decode_responses=decode_responses, **kwargs
        )
        return client

    if hasattr(aioredis, "from_url"):
        pool = await aioredis.from_url(dsn, decode_responses=decode_responses, **kwargs)
        return pool
    else:
        pool = await aioredis.create_redis_pool(dsn, **kwargs)
        return pool


async def close_redis(client):
    if client is None:
        return

    if _BACKEND == "redis":
        try:
            await client.close()
            await client.wait_closed()
        except Exception:
            pass
    else:
        try:
            client.close()
        except Exception:
            pass
        try:
            await client.wait_closed()
        except Exception:
            pass
