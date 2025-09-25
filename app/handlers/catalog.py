from aiogram import Router, types
from aiogram.types import CallbackQuery
from app.services.catalog import CatalogService
from app.keyboards.catalog import build_catalog_markup, CatalogCB
from app.repos.purchase import PendingRepository
from app.services.db import get_session

def get_catalog_router(async_session_maker, admin_ids, ranks) -> Router:
    service = CatalogService(admin_ids=admin_ids)

    router = Router()

    @router.callback_query(CatalogCB.filter())
    async def cb_handler(callback: CallbackQuery, callback_data=CatalogCB.filter()):
        data = callback_data
        action = data.action
        node_id = data.node_id
        purchase_id = data.purchase_id
        user_id = callback.from_user.id

        if action == "open":
            node = await service.find_node(node_id)
            if not node:
                await callback.answer("Узел не найден", show_alert=True)
                return
            markup = await build_catalog_markup(node, include_back=True)
            try:
                await callback.message.edit_text(f"📂 <b>{node.get('title')}</b>\nВыберите:", reply_markup=markup)
            except Exception:
                await callback.message.answer(f"📂 <b>{node.get('title')}</b>\nВыберите:", reply_markup=markup)
            await callback.answer()
            return

        if action == "product":
            product = await service.find_node(node_id)
            if not product:
                await callback.answer("Товар не найден", show_alert=True)
                return

            try:
                async with get_session(async_session_maker) as session:
                    purchase_id_new = await service.create_purchase(session, user_id, product)
            except Exception:
                await callback.answer("Ошибка при создании заявки", show_alert=True)
                return

            cb = CatalogCB(action="admin_confirm", node_id="", purchase_id=purchase_id_new)
            kb = {"inline_keyboard": [[{"text": "✅ Подтвердить оплату", "callback_data": cb.pack()}]]}
            admin_text = (
                f"🆕 <b>Новая заявка на покупку</b>\n"
                f"Пользователь: <code>{user_id}</code>\n"
                f"Товар: <b>{product.get('title')}</b>\n"
                f"Цена: {product.get('price', '—')}\n"
                f"purchase_id: <code>{purchase_id_new}</code>\n\n"
                "Нажмите кнопку ниже после реальной оплаты для начисления бонусов."
            )
            for aid in (admin_ids or []):
                try:
                    await callback.bot.send_message(chat_id=aid, text=admin_text, reply_markup=kb)
                except Exception:
                    pass

            await callback.answer("Заявка отправлена администраторам")
            return

        if action == "admin_confirm":
            if admin_ids and callback.from_user.id not in admin_ids:
                await callback.answer("Только администратор может подтверждать оплату.", show_alert=True)
                return

            try:
                async with get_session(async_session_maker) as session:
                    points = await service.confirm_purchase(session, ranks, purchase_id, confirmed_by=callback.from_user.id)
                    
                    pending_repo = PendingRepository(session)
                    rec = await pending_repo.get(purchase_id)
            except Exception:
                await callback.answer("Ошибка при подтверждении", show_alert=True)
                return
            
            if points is None:
                await callback.answer("Заявка не найдена или уже обработана", show_alert=True)
                return

            try:
                await callback.message.edit_text(callback.message.text + f"\n\n✅ Подтверждено администратором <code>{callback.from_user.id}</code>. Начислено {points} баллов.")
            except Exception:
                pass

            try:
                if rec:
                    await callback.bot.send_message(rec.user_id if hasattr(rec, "user_id") else rec["user_id"],
                                                   (f"✅ Ваш платёж подтверждён. Вам начислено {points} баллов.\n"
                                                    f"Товар: {rec.product_title if hasattr(rec, 'product_title') else rec.get('product_title')}"))
            except Exception:
                pass

            await callback.answer("Пользователю начислены бонусы")
            return

    return router
