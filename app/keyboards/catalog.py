from typing import Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

class CatalogCB(CallbackData, prefix="catalog"):
    action: str
    node_id: str
    purchase_id: str = ""

async def product_button_text(prod: Dict) -> str:
    price_text = f" — {prod.get('price')}₽" if prod.get('price') else ""
    return f"🛍 {prod.get('title')}{price_text}"

async def build_catalog_markup(node: Dict, include_back: bool = False) -> InlineKeyboardMarkup:
    keyboard = []
    for it in node.get("items", []):
        if it.get("type") == "category":
            cb = CatalogCB(action="open", node_id=it["id"], purchase_id="")
            keyboard.append([InlineKeyboardButton(text=f"📁 {it['title']}", callback_data=cb.pack())])
        elif it.get("type") == "product":
            cb = CatalogCB(action="product", node_id=it["id"], purchase_id="")
            keyboard.append([InlineKeyboardButton(text=await product_button_text(it), callback_data=cb.pack())])
    if include_back and node.get("parent_id"):
        cb = CatalogCB(action="open", node_id=node["parent_id"], purchase_id="")
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=cb.pack())])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
