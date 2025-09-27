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


async def fill_custom_bonus(redis, user_id, product_id):
    user_key = f"user:custom:{user_id}"
    try:
        await redis.set(user_key, product_id, ex=600)
    except Exception:
        try:
            await redis.setex(user_key, 600, product_id)
        except Exception:
            pass


async def get_product_id(redis, user_key):
    product_id = None
    try:
        if redis is not None:
            val = await redis.get(user_key)
            if val:
                if isinstance(val, bytes):
                    product_id = val.decode("utf-8")
                else:
                    product_id = str(val)
        return product_id
    except Exception:
        product_id = None
        return product_id
