from typing import List
from datetime import datetime

def format_purchase_item(p) -> str:
    created = getattr(p, "created_at", None)
    created_s = created.strftime("%Y-%m-%d") if isinstance(created, datetime) else str(created)
    
    return f"• {getattr(p, 'product_title', '')} — {getattr(p, 'price', '')}₽ — +{getattr(p, 'awarded_points', '')} Бонусов — ({created_s})"

def build_history_text(purchases: List) -> str:
    if not purchases:
        return "Вы ещё ничего не покупали."
    lines = [format_purchase_item(p) for p in purchases]
    return "\n\n".join(lines)
