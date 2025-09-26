from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from app.services.db import get_session
from app.repos.user import UserRepository
from pathlib import Path
from typing import List
from sqlalchemy import text


def get_admin_router(
    ranks,
    async_session_maker,
    catalog,
    redis=None,
    admin_ids: List[int] = None,
    ranks_file: Path = None,
    catalog_file: Path = None,
) -> Router:
    router = Router()

    @router.message(Command("commands"))
    async def cmd_reload(message: types.Message):
        uid = message.from_user.id if message.from_user else None
        if admin_ids and uid not in admin_ids:
            await message.reply("Доступ запрещён.")
            return router
        await message.reply(admin_commands_help_text)

    @router.message(Command("reload_ranks"))
    async def cmd_reload_ranks(message: types.Message):
        uid = message.from_user.id if message.from_user else None
        if admin_ids and uid not in admin_ids:
            await message.reply("Доступ запрещён.")
            return router
        if not ranks_file:
            await message.reply("Файл рангов не настроен.")
            return router
        try:
            await ranks.reload(ranks_file)
            await message.reply("Ранги перезагружены.")
        except Exception as e:
            await message.reply(f"Ошибка: {e}")

    @router.message(Command("reload_catalog"))
    async def cmd_reload_catalog(message: types.Message):
        uid = message.from_user.id if message.from_user else None
        if admin_ids and uid not in admin_ids:
            await message.reply("Доступ запрещён.")
            return router
        if not catalog_file:
            await message.reply("Файл каталога не настроен.")
            return router
        try:
            await catalog.reload(catalog_file)
            await message.reply("Каталог перезагружен.")
        except Exception as e:
            await message.reply(f"Ошибка: {e}")

    @router.message(Command("health"))
    async def cmd_health(message: types.Message):
        uid = message.from_user.id if message.from_user else None
        if admin_ids and uid not in admin_ids:
            await message.reply("Доступ запрещён.")
            return router

        ok = True
        parts = []

        try:
            async with get_session(async_session_maker) as s:
                await s.execute(text("SELECT 1"))
            parts.append("DB: OK")
        except Exception as e:
            ok = False
            parts.append(f"DB: ERR ({e})")

        if redis:
            try:
                pong = await redis.ping()
                parts.append("Redis: OK" if pong else "Redis: NO_PONG")
            except Exception as e:
                ok = False
                parts.append(f"Redis: ERR ({e})")

        await message.reply(("OK\n" if ok else "NOT OK\n") + "\n".join(parts))

    @router.message(Command("broadcast"))
    async def cmd_broadcast(message: types.Message, command: CommandObject):
        uid = message.from_user.id if message.from_user else None
        if admin_ids and uid not in admin_ids:
            await message.reply("Доступ запрещён.")
            return router

        text = command.args
        if not text:
            await message.reply("Usage: /broadcast 'message'")
            return router
        sent = 0
        async with get_session(async_session_maker) as s:
            repo = UserRepository(s)
            users = await repo.list_all()
            for u in users:
                try:
                    await message.bot.send_message(u.tg_id, text)
                    sent += 1
                except Exception:
                    continue
        await message.reply(f"Рассылка отправлена примерно {sent} пользователям.")

    @router.message(Command("add_bonus_points"))
    async def cmd_add_points(message: types.Message, command: CommandObject):
        uid = message.from_user.id if message.from_user else None
        if admin_ids and uid not in admin_ids:
            await message.reply("Доступ запрещён.")
            return router

        args = command.args
        if not args:
            await message.reply("Использование: /add_bonus_points 'tg_id' 'delta'")
            return router

        parts = args.split()
        if len(parts) != 2:
            await message.reply("Неверный формат. Пример: /add_bonus_points 123 1")
            return router

        try:
            tg_id = int(parts[0])
            delta = int(parts[1])
        except ValueError:
            await message.reply("Аргументы должны быть целыми числами.")
            return router

        try:
            async with get_session(async_session_maker) as s:
                repo = UserRepository(s)
                user = await repo.get_by_tg_id(tg_id)
                user = await repo.add_bonus_points(tg_id=tg_id, delta=delta)
                await message.reply(
                    f"Готово: {tg_id} теперь имеет {user.bonus_points} бонусных очков."
                )

        except Exception as e:
            await message.reply(f"Ошибка при обновлении: {e}")
            return router

    @router.message(Command("add_rank_points"))
    async def cmd_add_points(message: types.Message, command: CommandObject):
        uid = message.from_user.id if message.from_user else None
        if admin_ids and uid not in admin_ids:
            await message.reply("Доступ запрещён.")
            return router

        args = command.args
        if not args:
            await message.reply("Использование: /add_rank_points 'tg_id' 'delta'")
            return router

        parts = args.split()
        if len(parts) != 2:
            await message.reply("Неверный формат. Пример: /add_rank_points 123 1")
            return router

        try:
            tg_id = int(parts[0])
            delta = int(parts[1])
        except ValueError:
            await message.reply("Аргументы должны быть целыми числами.")
            return router

        try:
            async with get_session(async_session_maker) as s:
                repo = UserRepository(s)
                user = await repo.get_by_tg_id(tg_id)
                user = await repo.add_rank_points(tg_id=tg_id, delta=delta)
                await message.reply(
                    f"Готово: {tg_id} теперь имеет {user.rank_points} очков ранга."
                )

        except Exception as e:
            await message.reply(f"Ошибка при обновлении: {e}")
            return router

    return router


admin_commands_help_text = "\
/reload_ranks - Перезаргрузить ранги\n\
/reload_catalog - Перезаргрузить каталог товаров\n\
/health - Проверить работоспособность redis и postgres\n\
/broadcast 'text' - Запустить сообщение всем юзерам\n\
/add_bonus_points 'tg_id' 'value' -  Добавить пользователю n бонус-очков\n\
/add_rank_points 'tg_id' 'value' -  Добавить пользователю n ранг-очков"
