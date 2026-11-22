"""Правила доступа к операциям прикладных сервисов."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from olympiad_access.domain.permissions import OPERATIONS, allows_operation
from olympiad_access.services.auth import AuthService


class AccessService:
    """Проверяет права на операции других сервисов."""

    def __init__(self, db: AsyncSession) -> None:
        self.auth = AuthService(db)

    async def check_access(self, token: str, operation: str) -> UUID | None:
        """Возвращает идентификатор аккаунта при разрешённой операции."""
        if not token or operation not in OPERATIONS:
            return None
        principal = await self.auth.get_principal(token)
        if principal is None or not allows_operation(principal.role, operation):
            return None
        return principal.account_id
