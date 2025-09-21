from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager

def make_engine_and_session(dsn: str):
    """
    Создаём async engine для PostgreSQL (asyncpg).
    Настройки пула можно менять под нагрузку.
    """
    engine = create_async_engine(
        dsn,
        future=True,
        echo=False,
        pool_size=10,        # базовый пул соединений
        max_overflow=20,     # дополнительные временные соединения
        pool_timeout=30,     # сек для ожидания свободного соединения
        pool_pre_ping=True,  # проверяем живость соединения
    )
    
    
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    return engine, async_session

@asynccontextmanager
async def get_session(session_maker):
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
