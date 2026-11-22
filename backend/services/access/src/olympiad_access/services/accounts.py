"""Управление аккаунтами."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from olympiad_access.core.security import hash_password
from olympiad_access.domain.roles import RoleCode
from olympiad_access.exceptions.access import (
    AccountNotFound,
    AdminAlreadyExists,
    DuplicateLogin,
    Forbidden,
    InvalidAccountData,
    InvalidCredentials,
)
from olympiad_access.models.accounts import Account
from olympiad_access.repositories.accounts import insert_account, role_is_assigned, update_role
from olympiad_access.repositories.roles import lock_role_id, role_exists
from olympiad_access.services.auth import get_principal
from olympiad_access.validators.credentials import normalize_login, validate_password


async def bootstrap_admin(db: AsyncSession, login: str, password: str) -> None:
    """Создаёт первого администратора и защищает от одновременного запуска скрипта."""
    login = normalize_login(login)
    password_hash = await hash_password(validate_password(password))
    async with db.begin():
        admin_role = await lock_role_id(db, RoleCode.ADMIN)
        if await role_is_assigned(db, admin_role):
            raise AdminAlreadyExists("Аккаунт администратора уже существует.")
        if await insert_account(db, login, password_hash, admin_role) is None:
            raise DuplicateLogin("Логин уже занят.")


async def require_admin(db: AsyncSession, token: str) -> None:
    """Проверяет, что текущая сессия принадлежит администратору."""
    principal = await get_principal(db, token)
    if principal is None:
        raise InvalidCredentials()
    if principal.role != RoleCode.ADMIN:
        raise Forbidden("Операция доступна администратору.")


async def create_account(
    db: AsyncSession, token: str, login: str, password: str, role_id: int
) -> Account:
    """Создаёт аккаунт с назначенной администратором ролью."""
    async with db.begin():
        await require_admin(db, token)
        normalized_login = normalize_login(login)
        await ensure_role(db, role_id)
        password_hash = await hash_password(validate_password(password))
        account = await insert_account(db, normalized_login, password_hash, role_id)
        if account is None:
            raise DuplicateLogin("Логин уже занят.")
    return account


async def change_role(db: AsyncSession, token: str, account_id: UUID, role_id: int) -> Account:
    """Меняет роль аккаунта. Существующие сессии используют новое значение."""
    async with db.begin():
        await require_admin(db, token)
        await ensure_role(db, role_id)
        account = await update_role(db, account_id, role_id)
        if account is None:
            raise AccountNotFound("Аккаунт не найден.")
    return account


async def ensure_role(db: AsyncSession, role_id: int) -> None:
    """Проверяет, что роль существует в справочнике."""
    if not await role_exists(db, role_id):
        raise InvalidAccountData("Роль с указанным идентификатором отсутствует.")
