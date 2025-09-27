from aiogram import Router, types
from aiogram.types import CallbackQuery
from typing import Optional

from app.services.catalog import CatalogService
from app.keyboards.catalog import (
    build_catalog_markup,
    CatalogCB,
    RedeemCB,
    build_user_redeem_markup,
)
from app.services.catalog import check_balance_or_product, create_purchase_request
from app.services.admin import make_admin_confirm_message, admin_confirm_purchase
from app.services.redis import fill_custom_bonus, get_product_id
from app.services.user import get_user_bonus
from app.services.text import get_bonus_value_from_message


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

            user_bonus = await get_user_bonus(async_session_maker, user_id)

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

            await admin_confirm_purchase(
                async_session_maker, purchase_id, callback, service, ranks
            )

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
            user_bonus = await get_user_bonus(async_session_maker, user_id)
            redeemed_bonus = min(user_bonus, product_price)

        elif choice == "custom":
            if redis is not None:
                await fill_custom_bonus(redis, user_id, product_id)
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

        purchase_id_new = await create_purchase_request(
            async_session_maker,
            service,
            user_id,
            product,
            redeemed_bonus,
            redis,
            callback=callback,
        )

        await make_admin_confirm_message(
            purchase_id_new,
            product,
            product_price,
            redeemed_bonus,
            admin_ids,
            user_id,
            redis,
            callback=callback,
        )

    @router.message()
    async def on_user_custom_amount(message: types.Message):
        user_id = message.from_user.id
        user_key = f"user:custom:{user_id}"
        product_id = await get_product_id(redis, user_key)

        if not product_id:
            return

        amt = await get_bonus_value_from_message(message)

        product, product_price, user_bonus = await check_balance_or_product(
            async_session_maker, service, message, product_id, redis, user_id, user_key
        )

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

        purchase_id_new = await create_purchase_request(
            async_session_maker,
            service,
            user_id,
            product,
            amt,
            redis,
            user_key,
            message=message,
        )

        await make_admin_confirm_message(
            purchase_id_new,
            product,
            product_price,
            amt,
            admin_ids,
            user_id,
            redis,
            user_key,
            message=message,
        )

    return router
