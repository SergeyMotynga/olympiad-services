"""Управление аккаунтами."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from olympiad_access.domain import (
    AccountNotFound,
    AdminAlreadyExists,
    DuplicateLogin,
    Forbidden,
    InvalidCredentials,
    RoleCode,
)
from olympiad_access.models import Account
from olympiad_access.repositories import insert_account, role_id, role_is_assigned, update_role
from olympiad_access.security import hash_password, normalize_login
from olympiad_access.services.auth import get_principal


async def bootstrap_admin(db: AsyncSession, login: str, password: str) -> None:
    """Создаёт первого администратора и защищает от одновременного запуска скрипта."""
    login = normalize_login(login)
    password_hash = await hash_password(password)
    async with db.begin():
        admin_role = await role_id(db, RoleCode.ADMIN, lock=True)
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
    db: AsyncSession, token: str, login: str, password: str, role: RoleCode
) -> Account:
    """Создаёт аккаунт с назначенной администратором ролью."""
    async with db.begin():
        await require_admin(db, token)
        normalized_login = normalize_login(login)
        assigned_role = await role_id(db, role)
        password_hash = await hash_password(password)
        account = await insert_account(db, normalized_login, password_hash, assigned_role)
        if account is None:
            raise DuplicateLogin("Логин уже занят.")
    return account


async def change_role(db: AsyncSession, token: str, account_id: UUID, role: RoleCode) -> Account:
    """Меняет роль аккаунта. Существующие сессии используют новое значение."""
    async with db.begin():
        await require_admin(db, token)
        account = await update_role(db, account_id, await role_id(db, role))
        if account is None:
            raise AccountNotFound("Аккаунт не найден.")
    return account
