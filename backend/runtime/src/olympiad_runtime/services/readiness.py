"""Правила проверки готовности приложения."""

from asyncio import timeout

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from olympiad_runtime.repositories.database import ping_database


async def is_database_ready(database: AsyncEngine) -> bool:
    """Проверяет доступность базы с ограничением времени ожидания."""
    try:
        async with timeout(3):
            await ping_database(database)
    except (SQLAlchemyError, OSError, TimeoutError):
        return False
    return True
