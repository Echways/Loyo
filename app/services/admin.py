from app.keyboards.catalog import build_admin_confirm_kb
from app.services.db import get_session
from app.repos.purchase import PendingRepository


async def make_admin_confirm_message(
    purchase_id_new: str,
    product,
    product_price,
    amt,
    admin_ids,
    user_id,
    redis,
    user_key=None,
    message=None,
    callback=None,
):
    if message is not None:
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

    elif callback is not None:
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


async def admin_confirm_purchase(
    async_session_maker, purchase_id, callback, service, ranks
):
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
        await callback.answer("Заявка не найдена или уже обработана", show_alert=True)
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
                uid = rec2.user_id if hasattr(rec2, "user_id") else rec2.get("user_id")
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
