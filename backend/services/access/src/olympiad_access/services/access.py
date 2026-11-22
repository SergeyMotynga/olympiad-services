"""Правила доступа к операциям прикладных сервисов."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from olympiad_access.domain.roles import RoleCode
from olympiad_access.services.auth import get_principal

OPERATIONS = {
    "tasks:list": RoleCode.AUTHOR,
    "tasks:create": RoleCode.AUTHOR,
    "tasks:update": RoleCode.AUTHOR,
    "tasks:print": RoleCode.ADMIN,
    "submissions:open": RoleCode.ADMIN,
    "submissions:list": RoleCode.REPRESENTATIVE,
    "submissions:create": RoleCode.REPRESENTATIVE,
    "submissions:update": RoleCode.REPRESENTATIVE,
}


async def check_access(db: AsyncSession, token: str, operation: str) -> UUID | None:
    """Возвращает идентификатор аккаунта при разрешённой операции."""
    required_role = OPERATIONS.get(operation)
    if not token or required_role is None:
        return None
    principal = await get_principal(db, token)
    if principal is None or principal.role not in (RoleCode.ADMIN, required_role):
        return None
    return principal.account_id
