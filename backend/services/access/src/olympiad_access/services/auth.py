"""Вход и хранение сессий."""

from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

from sqlalchemy.ext.asyncio import AsyncSession

from olympiad_access.core.security import hash_token, verify_password
from olympiad_access.domain.roles import RoleCode
from olympiad_access.dto.auth import IssuedSession, Principal
from olympiad_access.exceptions.access import Forbidden, InvalidAccountData, InvalidCredentials
from olympiad_access.repositories.accounts import AccountRepository
from olympiad_access.repositories.sessions import SessionRepository
from olympiad_access.validators.credentials import normalize_login

SESSION_TTL = timedelta(days=7)


class AuthService:
    """Управляет входом, сессиями и текущей ролью."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.accounts = AccountRepository(db)
        self.sessions = SessionRepository(db)

    async def login(self, login: str, password: str) -> IssuedSession:
        """Проверяет пароль и создаёт независимую сессию."""
        try:
            normalized_login = normalize_login(login)
        except InvalidAccountData as error:
            raise InvalidCredentials() from error

        async with self.db.begin():
            account = await self.accounts.find_account_by_login(normalized_login)
            account_id = account.id if account else None
            stored_hash = account.password_hash if account else None

        if not await verify_password(password, stored_hash) or account_id is None:
            raise InvalidCredentials()

        token = token_urlsafe(32)
        now = datetime.now(UTC)
        expires_at = now + SESSION_TTL
        async with self.db.begin():
            await self.sessions.insert_session(account_id, hash_token(token), now, expires_at)
        return IssuedSession(token, expires_at)

    async def logout(self, token: str) -> None:
        """Отзывает только сессию, которой принадлежит переданный токен."""
        async with self.db.begin():
            if not await self.sessions.revoke_session(hash_token(token), datetime.now(UTC)):
                raise InvalidCredentials()

    async def get_principal(self, token: str) -> Principal | None:
        """Ищет действующую сессию и читает роль из аккаунта."""
        account = await self.sessions.find_session_account(hash_token(token), datetime.now(UTC))
        if account is None:
            return None
        account_id, code = account
        return Principal(account_id, RoleCode(code))

    async def require_admin(self, token: str) -> None:
        """Проверяет, что текущая сессия принадлежит администратору."""
        principal = await self.get_principal(token)
        if principal is None:
            raise InvalidCredentials()
        if principal.role != RoleCode.ADMIN:
            raise Forbidden("Операция доступна администратору.")
