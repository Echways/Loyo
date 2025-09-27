import json
import pytest

from app.services.ranks import RanksStore
from app.services.text import get_bonus_value_from_message

pytest_plugins = ("pytest_asyncio",)


class FakeRedis:
    def __init__(self):
        self._store = {}

    async def set(self, key, value):
        self._store[key] = value

    async def get(self, key):
        return self._store.get(key)


@pytest.mark.asyncio
async def test_load_from_file_writes_to_redis_and_orders_ranks(tmp_path):
    data = [
        {"min": "100", "max": "199", "name": "Silver", "cashback": "5"},
        {"min_points": 0, "max_points": 99, "title": "Bronze", "cashback_percent": 0},
        {"min": 200, "max": 999, "name": "Gold", "cashback_percent": 10},
    ]

    p = tmp_path / "ranks.json"
    p.write_text(json.dumps(data, ensure_ascii=False))

    fake_redis = FakeRedis()
    store = RanksStore(redis=fake_redis)

    await store.load_from_file(p)

    ranks = await store.all_ranks()
    assert [r.min_points for r in ranks] == [0, 100, 200]

    raw = await fake_redis.get("ranks:data")
    assert raw is not None
    parsed = json.loads(raw)
    assert any(r.get("title") == "Bronze" or r.get("name") == "Bronze" for r in parsed)


@pytest.mark.asyncio
async def test_load_from_nonexistent_file_raises(tmp_path):
    store = RanksStore()
    missing = tmp_path / "does_not_exist.json"
    with pytest.raises(FileNotFoundError):
        await store.load_from_file(missing)


@pytest.mark.asyncio
async def test_get_rank_by_points_boundaries(tmp_path):
    data = [
        {"min_points": 0, "max_points": 9, "name": "A", "cashback_percent": 1},
        {"min_points": 10, "max_points": 19, "name": "B", "cashback_percent": 2},
    ]
    p = tmp_path / "ranks2.json"
    p.write_text(json.dumps(data))

    store = RanksStore()
    await store.load_from_file(p)

    r = await store.get_rank_by_points(0)
    assert r is not None and r.name == "A"

    r = await store.get_rank_by_points(9)
    assert r is not None and r.name == "A"

    r = await store.get_rank_by_points(10)
    assert r is not None and r.name == "B"

    r = await store.get_rank_by_points(1000)
    assert r is not None and r.name == "B"


@pytest.mark.asyncio
async def test_get_cashback_and_range_and_none(tmp_path):
    data = [
        {"min_points": 0, "max_points": 9, "name": "A", "cashback_percent": 1},
        {"min_points": 10, "max_points": 19, "name": "B", "cashback_percent": 2},
    ]
    p = tmp_path / "ranks3.json"
    p.write_text(json.dumps(data))

    store = RanksStore()
    await store.load_from_file(p)

    assert await store.get_cashback_percent_by_points(5) == 1
    assert await store.get_cashback_percent_by_points(10) == 2

    assert await store.get_rank_points_range_by_points(4) == [0, 9]
    assert await store.get_rank_points_range_by_points(10) == [10, 19]

    assert await store.get_rank_points_range_by_points(-5) is None


@pytest.mark.asyncio
async def test_get_bonus_value_from_message_valid_and_invalid():
    class Msg:
        def __init__(self, text):
            self.text = text
            self.replied_with = None

        async def reply(self, text):
            self.replied_with = text

    m_valid = Msg("123")
    res = await get_bonus_value_from_message(m_valid)
    assert res == 123

    m_invalid = Msg("abc")
    res2 = await get_bonus_value_from_message(m_invalid)
    assert res2 is None
    assert m_invalid.replied_with is not None

    m_negative = Msg("-5")
    res3 = await get_bonus_value_from_message(m_negative)
    assert res3 is None
    assert m_negative.replied_with is not None
