from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import uuid
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect
from app.repos.purchase import PendingRepository, PurchaseHistoryRepo
from app.repos.user import UserRepository

rank_points_coefficent = 0.01

class CatalogService:
    def __init__(self, admin_ids: Optional[list] = None, catalog_path: Optional[str] = None):
        base = Path(__file__).resolve().parents[1]
        data_dir = base.parent / "data"
        self.catalog_path = str(Path(catalog_path) if catalog_path else (data_dir / "catalog.json"))
        self.admin_ids = admin_ids or []

        if not Path(self.catalog_path).exists():
            Path(self.catalog_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump({"id": "root", "title": "Каталог", "items": []}, f, ensure_ascii=False, indent=2)
        cat = self.load_catalog()
        self._normalize_parents(cat, parent_id=None)
        with open(self.catalog_path, "w", encoding="utf-8") as f:
            json.dump(cat, f, ensure_ascii=False, indent=2)

    def load_catalog(self) -> Dict[str, Any]:
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def find_node(self, node_id: str, node: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if node is None:
            node = self.load_catalog()
        if node.get("id") == node_id:
            return node
        for it in node.get("items", []):
            if it.get("id") == node_id:
                return it
            if it.get("type") == "category":
                found = self.find_node(node_id, it)
                if found:
                    return found
        return None

    def _normalize_parents(self, node: Dict[str, Any], parent_id: Optional[str]):
        node["parent_id"] = parent_id
        for it in node.get("items", []):
            if it.get("type") == "category":
                self._normalize_parents(it, node.get("id"))
            else:
                it["parent_id"] = node.get("id")
                
    async def create_purchase(self, session: AsyncSession, user_id: int, product_node: Dict[str, Any]) -> str:
        pending_repo = PendingRepository(session)
        history_repo = PurchaseHistoryRepo(session)

        purchase_id = str(uuid.uuid4())
        now = datetime.now()
        record = {
            "purchase_id": purchase_id,
            "user_id": user_id,
            "product_id": product_node.get("id"),
            "product_title": product_node.get("title"),
            "price": product_node.get("price"),
            "status": "waiting",
            "created_at": now,
            "payload": product_node
        }
        await pending_repo.create(record)
        await history_repo.insert_if_present({
            "purchase_id": purchase_id,
            "user_id": user_id,
            "product_id": product_node.get("id"),
            "product_title": product_node.get("title"),
            "price": product_node.get("price"),
            "status": "waiting",
            "payload": product_node,
            "created_at": now
        })
        return purchase_id

    async def confirm_purchase(self, session: AsyncSession, ranks, purchase_id: str, confirmed_by: int) -> Optional[int]:
        pending_repo = PendingRepository(session)
        history_repo = PurchaseHistoryRepo(session)
        user_repo = UserRepository(session)
        
        rec = await pending_repo.get(purchase_id)
        if not rec or rec.status != "waiting":
            return None
        
        async def serialize_instance(obj):
            result = {}
            for c in inspect(obj).mapper.column_attrs:
                val = getattr(obj, c.key)
                if isinstance(val, datetime):
                    val = val.isoformat()
                result[c.key] = val
            return result

        price = int(rec.price or 0)
        
        user_item = await user_repo.get_by_tg_id(rec.user_id)
        rank_item = await ranks.get_rank_by_points(user_item.rank_points)
        cashback = rank_item.cashback_percent/100
        
        bonus_points = max(1, int(price*cashback)) if price > 0 else 1
        rank_points = max(1, int(price*rank_points_coefficent)) if price > 0 else 1

        await user_repo.add_bonus_points(rec.user_id, bonus_points)
        await user_repo.add_rank_points(rec.user_id, rank_points)
        await pending_repo.mark_confirmed(purchase_id, confirmed_by, bonus_points)

        payload = await serialize_instance(rec)

        await history_repo.update_if_present(purchase_id, {
            "status": "confirmed",
            "confirmed_by": confirmed_by,
            "awarded_points": bonus_points,
            "confirmed_at": datetime.now(),
            "payload": payload
        })

        return bonus_points
    