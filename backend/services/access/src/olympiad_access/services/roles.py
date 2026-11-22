"""Получение справочника ролей."""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from olympiad_access.models.accounts import Role
from olympiad_access.repositories.roles import RoleRepository
from olympiad_access.services.auth import AuthService


class RoleService:
    """Предоставляет администратору справочник ролей."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.roles = RoleRepository(db)
        self.auth = AuthService(db)

    async def get_roles(self, token: str) -> Sequence[Role]:
        """Возвращает роли после проверки прав администратора."""
        async with self.db.begin():
            await self.auth.require_admin(token)
            return await self.roles.list_roles()
