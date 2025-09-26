from aiogram import Router, types
from aiogram.types import CallbackQuery
from typing import Optional

from app.services.catalog import CatalogService
from app.keyboards.catalog import (
    build_catalog_markup,
    CatalogCB,
    RedeemCB,
    build_user_redeem_markup,
    build_admin_confirm_kb,
)
from app.repos.purchase import PendingRepository
from app.repos.user import UserRepository
from app.services.db import get_session


def get_catalog_router(
    async_session_maker, admin_ids, ranks, redis: Optional[object] = None
) -> Router:
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
                await callback.message.edit_text(
                    f"📂 <b>{node.get('title')}</b>\nВыберите:", reply_markup=markup
                )
            except Exception:
                await callback.message.answer(
                    f"📂 <b>{node.get('title')}</b>\nВыберите:", reply_markup=markup
                )
            await callback.answer()
            return

        if action == "product":
            product = await service.find_node(node_id)
            if not product:
                await callback.answer("Товар не найден", show_alert=True)
                return

            user_bonus = 0
            try:
                async with get_session(async_session_maker) as session:
                    user_repo = UserRepository(session)
                    user = await user_repo.get_by_tg_id(user_id)
                    user_bonus = (
                        int(user.bonus_points)
                        if user and getattr(user, "bonus_points", None) is not None
                        else 0
                    )
            except Exception:
                user_bonus = 0

            markup = build_user_redeem_markup(node_id)
            product_text = (
                f"🛍 <b>{product.get('title')}</b>\n"
                f"Цена: {product.get('price', '—')}₽\n"
                f"Ваш доступный баланс бонусов: <b>{user_bonus}</b>.\n\n"
                "Выберите, хотите ли вы списать бонусы при покупке:"
            )
            try:
                await callback.message.edit_text(product_text, reply_markup=markup)
            except Exception:
                await callback.message.answer(product_text, reply_markup=markup)
            await callback.answer()
            return

        if action == "admin_confirm":
            if admin_ids and callback.from_user.id not in admin_ids:
                await callback.answer(
                    "Только администратор может подтверждать оплату.", show_alert=True
                )
                return

            try:
                async with get_session(async_session_maker) as session:
                    pending_repo = PendingRepository(session)
                    rec = await pending_repo.get(purchase_id)
                    if not rec:
                        await callback.answer("Заявка не найдена", show_alert=True)
                        return

                    redeemed_bonus = 0
                    try:
                        payload = rec.payload or {}
                        orig_price = int(
                            payload.get("price")
                            if payload and payload.get("price") is not None
                            else 0
                        )
                        after_price = int(rec.price or 0)
                        redeemed_bonus = max(0, orig_price - after_price)
                    except Exception:
                        redeemed_bonus = 0

                    points = await service.confirm_purchase(
                        session,
                        ranks,
                        purchase_id,
                        confirmed_by=callback.from_user.id,
                        redeemed_bonus=redeemed_bonus,
                    )
            except Exception:
                await callback.answer("Ошибка при подтверждении", show_alert=True)
                return

            if points is None:
                await callback.answer(
                    "Заявка не найдена или уже обработана", show_alert=True
                )
                return

            try:
                await callback.message.edit_text(
                    callback.message.text
                    + f"\n\n✅ Подтверждено администратором <code>{callback.from_user.id}</code>."
                    f" Списано {redeemed_bonus} бонусов. Начислено {points} баллов."
                )
            except Exception:
                pass

            try:
                pending_repo = PendingRepository(session) if False else None
                async with get_session(async_session_maker) as session2:
                    pending_repo2 = PendingRepository(session2)
                    rec2 = await pending_repo2.get(purchase_id)
                    if rec2:
                        uid = (
                            rec2.user_id
                            if hasattr(rec2, "user_id")
                            else rec2.get("user_id")
                        )
                        product_title = (
                            rec2.product_title
                            if hasattr(rec2, "product_title")
                            else rec2.get("product_title")
                        )
                        await callback.bot.send_message(
                            uid,
                            (
                                f"✅ Ваш платёж подтверждён. Вам начислено {points} баллов.\n"
                                f"Товар: {product_title}\n"
                                f"Списано бонусов: {redeemed_bonus}"
                            ),
                        )
            except Exception:
                pass

            await callback.answer("Пользователю начислены бонусы")
            return

    @router.callback_query(RedeemCB.filter())
    async def redeem_choice_handler(
        callback: CallbackQuery, callback_data=RedeemCB.filter()
    ):
        data = callback_data
        choice = data.choice
        product_id = data.product_id
        user_id = callback.from_user.id

        if choice == "cancel":
            try:
                await callback.message.edit_text(
                    callback.message.text + "\n\n🛑 Покупка отменена."
                )
            except Exception:
                pass
            await callback.answer("Отменено")
            return

        product = await service.find_node(product_id)
        if not product:
            await callback.answer("Товар не найден", show_alert=True)
            return

        product_price = int(product.get("price") or 0)
        redeemed_bonus = 0

        if choice == "none":
            redeemed_bonus = 0

        elif choice == "all":
            try:
                async with get_session(async_session_maker) as session:
                    user_repo = UserRepository(session)
                    user = await user_repo.get_by_tg_id(user_id)
                    user_bonus = (
                        int(user.bonus_points)
                        if user and getattr(user, "bonus_points", None) is not None
                        else 0
                    )
                    redeemed_bonus = min(user_bonus, product_price)
            except Exception:
                redeemed_bonus = 0

        elif choice == "custom":
            if redis is not None:
                user_key = f"user:custom:{user_id}"
                try:
                    await redis.set(user_key, product_id, ex=600)
                except Exception:
                    try:
                        await redis.setex(user_key, 600, product_id)
                    except Exception:
                        pass
            try:
                await callback.message.reply(
                    f"✏️ Введите число бонусов, которые вы хотите списать для товара <b>{product.get('title')}</b>.\n"
                    f"Цена товара: {product_price}₽. Чтобы списать, у вас должно быть не менее нужного количества бонусов.\n"
                    "Отправьте целое число >= 0. Чтобы отменить — нажмите кнопку Отмена."
                )
            except Exception:
                pass
            await callback.answer("Введите сумму бонусов в сообщении")
            return

        if redeemed_bonus > product_price:
            redeemed_bonus = product_price

        try:
            async with get_session(async_session_maker) as session:
                purchase_id_new = await service.create_purchase(
                    session, user_id, product, redeemed_bonus
                )
        except Exception:
            await callback.answer("Ошибка при создании заявки", show_alert=True)
            return

        kb = build_admin_confirm_kb(purchase_id_new)
        orig_price = product_price
        after_price = max(0, orig_price - redeemed_bonus)
        admin_text = (
            f"🆕 <b>Новая заявка на покупку</b>\n"
            f"Пользователь: <code>#{user_id}</code>\n"
            f"Товар: <b>{product.get('title')}</b>\n"
            f"Исходная цена: {orig_price}₽\n"
            f"Списано бонусов: {redeemed_bonus}₽\n"
            f"Цена со списанием: {after_price}₽\n"
            f"purchase_id: <code>{purchase_id_new}</code>\n\n"
            "Нажмите кнопку ниже после реальной оплаты для начисления бонусов."
        )
        for aid in admin_ids or []:
            try:
                await callback.bot.send_message(
                    chat_id=aid, text=admin_text, reply_markup=kb
                )
            except Exception:
                pass

        try:
            await callback.message.edit_text(
                callback.message.text
                + "\n\n✅ Заявка создана и отправлена администраторам. Ожидайте подтверждения."
            )
        except Exception:
            pass

        await callback.answer("Заявка создана")

    @router.message()
    async def on_user_custom_amount(message: types.Message):
        user_id = message.from_user.id
        user_key = f"user:custom:{user_id}"
        product_id = None
        try:
            if redis is not None:
                val = await redis.get(user_key)
                if val:
                    if isinstance(val, bytes):
                        product_id = val.decode("utf-8")
                    else:
                        product_id = str(val)
        except Exception:
            product_id = None

        if not product_id:
            return

        text = (message.text or "").strip()
        try:
            amt = int(text)
            if amt < 0:
                raise ValueError()
        except Exception:
            await message.reply(
                "Неверный формат суммы. Отправьте неотрицательное целое число."
            )
            return

        try:
            product = await service.find_node(product_id)
            if not product:
                await message.reply("Товар не найден / устарел.")
                try:
                    if redis is not None:
                        await redis.delete(user_key)
                except Exception:
                    pass
                return
            product_price = int(product.get("price") or 0)

            async with get_session(async_session_maker) as session:
                user_repo = UserRepository(session)
                user = await user_repo.get_by_tg_id(user_id)
                user_bonus = (
                    int(user.bonus_points)
                    if user and getattr(user, "bonus_points", None) is not None
                    else 0
                )
        except Exception:
            await message.reply(
                "Не удалось проверить баланс или товар — попробуйте позже."
            )
            try:
                if redis is not None:
                    await redis.delete(user_key)
            except Exception:
                pass
            return

        if amt > product_price:
            await message.reply(
                f"Нельзя списать больше, чем стоимость товара ({product_price}₽). Отправьте число не больше {product_price}."
            )
            return

        if amt > user_bonus:
            await message.reply(
                f"У вас недостаточно бонусов. Доступно: {user_bonus}. Отправьте число не больше {user_bonus}."
            )
            return

        try:
            async with get_session(async_session_maker) as session:
                purchase_id_new = await service.create_purchase(
                    session, user_id, product, amt
                )
        except Exception:
            await message.reply("Ошибка при создании заявки с вашей суммой.")
            try:
                if redis is not None:
                    await redis.delete(user_key)
            except Exception:
                pass
            return

        kb = build_admin_confirm_kb(purchase_id_new)
        orig_price = product_price
        after_price = max(0, orig_price - amt)
        admin_text = (
            f"🆕 <b>Новая заявка на покупку</b>\n"
            f"Пользователь: <code>#{user_id}</code>\n"
            f"Товар: <b>{product.get('title')}</b>\n"
            f"Исходная цена: {orig_price}₽\n"
            f"Списано бонусов: {amt}₽\n"
            f"Цена со списанием: {after_price}₽\n"
            f"purchase_id: <code>{purchase_id_new}</code>\n\n"
            "Нажмите кнопку ниже после реальной оплаты для начисления бонусов."
        )
        for aid in admin_ids or []:
            try:
                await message.bot.send_message(
                    chat_id=aid, text=admin_text, reply_markup=kb
                )
            except Exception:
                pass

        await message.reply(
            "✅ Заявка создана и отправлена администраторам. Ожидайте подтверждения."
        )
        try:
            if redis is not None:
                await redis.delete(user_key)
        except Exception:
            pass

    return router
