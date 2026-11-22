from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def build_engine(database_url: str) -> AsyncEngine:
    """Настраивает пул соединений с PostgreSQL."""
    return create_async_engine(database_url, pool_pre_ping=True)


async def ping_database(database: AsyncEngine) -> None:
    """Выполняет короткий запрос к базе."""
    async with database.connect() as connection:
        await connection.execute(text("SELECT 1"))
