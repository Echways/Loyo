import asyncio

from app.services.redis import get_product_id


def test_get_product_id_bytes_and_str_and_none():
    class FakeRedisBytes:
        async def get(self, key):
            return b"p_123"

    class FakeRedisStr:
        async def get(self, key):
            return "p_abc"

    class FakeRedisNone:
        async def get(self, key):
            return None

    assert asyncio.run(get_product_id(FakeRedisBytes(), "k")) == "p_123"
    assert asyncio.run(get_product_id(FakeRedisStr(), "k")) == "p_abc"
    assert asyncio.run(get_product_id(FakeRedisNone(), "k")) is None


def test_get_product_id_handles_exceptions():
    class BombRedis:
        async def get(self, key):
            raise RuntimeError("boom")

    assert asyncio.run(get_product_id(BombRedis(), "k")) is None
