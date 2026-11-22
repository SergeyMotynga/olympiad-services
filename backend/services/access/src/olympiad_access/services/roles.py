"""Получение справочника ролей."""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from olympiad_access.models.accounts import Role
from olympiad_access.repositories.roles import list_roles
from olympiad_access.services.accounts import require_admin


async def get_roles(db: AsyncSession, token: str) -> Sequence[Role]:
    """Возвращает роли после проверки прав администратора."""
    async with db.begin():
        await require_admin(db, token)
        return await list_roles(db)
