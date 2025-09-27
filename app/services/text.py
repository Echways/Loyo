async def get_bonus_value_from_message(message):
    text = (message.text or "").strip()
    try:
        amt = int(text)
        if amt < 0:
            raise ValueError()
        else:
            return amt
    except Exception:
        await message.reply(
            "Неверный формат суммы. Отправьте неотрицательное целое число."
        )
        return
