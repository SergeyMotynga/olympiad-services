"""Управление аккаунтами."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from olympiad_access.core.security import hash_password
from olympiad_access.domain.roles import RoleCode
from olympiad_access.exceptions.access import (
    AccountNotFound,
    AdminAlreadyExists,
    DuplicateLogin,
    InvalidAccountData,
)
from olympiad_access.models.accounts import Account
from olympiad_access.repositories.accounts import AccountRepository
from olympiad_access.repositories.roles import RoleRepository
from olympiad_access.services.auth import AuthService
from olympiad_access.validators.credentials import normalize_login, validate_password


class AccountService:
    """Создаёт аккаунты и назначает роли."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.accounts = AccountRepository(db)
        self.roles = RoleRepository(db)
        self.auth = AuthService(db)

    async def bootstrap_admin(self, login: str, password: str) -> None:
        """Создаёт первого администратора и защищает от одновременного запуска скрипта."""
        login = normalize_login(login)
        password_hash = await hash_password(validate_password(password))
        async with self.db.begin():
            admin_role = await self.roles.lock_role_id(RoleCode.ADMIN)
            if await self.accounts.role_is_assigned(admin_role):
                raise AdminAlreadyExists("Аккаунт администратора уже существует.")
            if await self.accounts.insert_account(login, password_hash, admin_role) is None:
                raise DuplicateLogin("Логин уже занят.")

    async def create_account(self, token: str, login: str, password: str, role_id: int) -> Account:
        """Создаёт аккаунт с назначенной администратором ролью."""
        async with self.db.begin():
            await self.auth.require_admin(token)
            normalized_login = normalize_login(login)
            await self._ensure_role(role_id)
            password_hash = await hash_password(validate_password(password))
            account = await self.accounts.insert_account(normalized_login, password_hash, role_id)
            if account is None:
                raise DuplicateLogin("Логин уже занят.")
        return account

    async def change_role(self, token: str, account_id: UUID, role_id: int) -> Account:
        """Меняет роль аккаунта. Существующие сессии используют новое значение."""
        async with self.db.begin():
            await self.auth.require_admin(token)
            await self._ensure_role(role_id)
            account = await self.accounts.update_role(account_id, role_id)
            if account is None:
                raise AccountNotFound("Аккаунт не найден.")
        return account

    async def _ensure_role(self, role_id: int) -> None:
        """Проверяет, что роль существует в справочнике."""
        if not await self.roles.role_exists(role_id):
            raise InvalidAccountData("Роль с указанным идентификатором отсутствует.")
