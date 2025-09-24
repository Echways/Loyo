from dataclasses import dataclass, asdict
from typing import List, Optional
import asyncio
import json
from pathlib import Path

@dataclass(frozen=True)
class RankItem:
    min_points: int
    max_points: int
    name: str
    cashback_percent: int

class RanksStore:
    def __init__(self, redis=None):
        self._ranks: List[RankItem] = []
        self._lock = asyncio.Lock()
        self._redis = redis

    async def load_from_file(self, path: Path):
        if not path.exists():
            raise FileNotFoundError(f"Ranks file not found: {path}")
        text = await asyncio.to_thread(path.read_text, "utf-8")
        data = json.loads(text)
        ranks: List[RankItem] = []
        for ent in data:
            min_p = int(ent.get("min_points") or ent.get("min") or 0)
            max_p = int(ent.get("max_points") or ent.get("max") or 0)
            name = str(ent.get("name") or ent.get("title") or "Unnamed")
            cashback_p = int(ent.get("cashback_percent") or ent.get("cashback") or 0)
            ranks.append(RankItem(min_points=min_p, max_points=max_p, name=name, cashback_percent=cashback_p))
        ranks.sort(key=lambda r: r.min_points)
        async with self._lock:
            self._ranks = ranks
        if self._redis is not None:
            try:
                metadata = json.dumps([asdict(r) for r in ranks], ensure_ascii=False)
                await self._redis.set("ranks:data", metadata)
            except Exception:
                pass

    async def get_rank_by_points(self, points: int) -> Optional[RankItem]:
        async with self._lock:
            for r in reversed(self._ranks):
                if points >= r.min_points:
                    return r
        return None
    
    async def get_rank_points_range_by_points(self, points: int) -> Optional[int | int]:
        res = [-1, -1]
        async with self._lock:
            for r in reversed(self._ranks):
                if points >= r.min_points:
                    res[0] = r.min_points
                    res[1] = r.max_points
                    return res
        return None
    
    async def get_cashback_percent_by_points(self, points: int) -> Optional[int]:
        async with self._lock:
            for r in reversed(self._ranks):
                if points >= r.min_points:
                    return r.cashback_percent
        return None

    async def all_ranks(self) -> List[RankItem]:
        async with self._lock:
            return list(self._ranks)

    async def reload(self, path: Path):
        await self.load_from_file(path)
