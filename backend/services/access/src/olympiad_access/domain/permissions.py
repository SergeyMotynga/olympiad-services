"""Права ролей на операции сервисов."""

from olympiad_access.domain.roles import RoleCode

LIST_ROLES = "roles:list"
CREATE_ACCOUNT = "accounts:create"
CHANGE_ACCOUNT_ROLE = "accounts:change_role"

OPERATIONS = {
    "tasks:list": RoleCode.AUTHOR,
    "tasks:create": RoleCode.AUTHOR,
    "tasks:update": RoleCode.AUTHOR,
    "tasks:print": RoleCode.ADMIN,
    "submissions:open": RoleCode.ADMIN,
    "submissions:list": RoleCode.REPRESENTATIVE,
    "submissions:create": RoleCode.REPRESENTATIVE,
    "submissions:update": RoleCode.REPRESENTATIVE,
    LIST_ROLES: RoleCode.ADMIN,
    CREATE_ACCOUNT: RoleCode.ADMIN,
    CHANGE_ACCOUNT_ROLE: RoleCode.ADMIN,
}


def allows_operation(role: RoleCode, operation: str) -> bool:
    """Проверяет право роли на известную операцию."""
    required_role = OPERATIONS.get(operation)
    return required_role is not None and role in (RoleCode.ADMIN, required_role)


def allowed_operations(role: RoleCode) -> tuple[str, ...]:
    """Возвращает коды всех операций, доступных роли."""
    return tuple(operation for operation in sorted(OPERATIONS) if allows_operation(role, operation))
