"""
Alembic env.py для асинхронного SQLAlchemy (asyncpg).
Поддерживает offline и online (async) режимы миграций.

ВАЖНО:
 - Убедись, что импорты моделей (Base) доступны — здесь пример: from app.models.base import Base
 - Перед запуском экспортируй переменную окружения DATABASE_URL, например:
     export DATABASE_URL=postgresql+asyncpg://bot:secret@db:5432/botdb
"""

from __future__ import annotations
import asyncio
from logging.config import fileConfig
import os
from sqlalchemy import pool
from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Импортируй метаданные ваших моделей сюда
# ---------------------------------------------------------------------------
# Пример: если у тебя declarative_base() находится в app/models/base.py
try:
    from app.models.base import Base  # <- обязательно поправь путь если у тебя другой
except Exception as ex:
    raise RuntimeError("Не удалось импортировать Base. Исправь путь в alembic/env.py") from ex

target_metadata = getattr(Base, "metadata", None)
# ---------------------------------------------------------------------------

# Опционально: получить URL из env var DATABASE_URL или из alembic.ini
def get_database_url() -> str:
    # Alembic ini содержит: sqlalchemy.url = %(DATABASE_URL)s (см. предложенный alembic.ini)
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url
    # fallback to value from alembic.ini (if configured)
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("DATABASE_URL не задан и sqlalchemy.url в alembic.ini отсутствует")
    return url

# -----------------------------------------------------------------------------
# Offline migrations (SQL script generation) — стандартный путь
# -----------------------------------------------------------------------------
def run_migrations_offline():
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # полезно, чтобы alembic видел изменения типов колонок
    )

    with context.begin_transaction():
        context.run_migrations()

# -----------------------------------------------------------------------------
# Online migrations (используем async engine и run_sync)
# -----------------------------------------------------------------------------
def do_run_migrations(connection: Connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    url = get_database_url()
    connectable = create_async_engine(url, poolclass=pool.NullPool)  # NullPool часто удобен для миграций
    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    # запускаем async путь
    asyncio.run(run_async_migrations())
