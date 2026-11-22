"""Вход и хранение сессий."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from olympiad_access.domain import InvalidAccountData, InvalidCredentials, RoleCode
from olympiad_access.repositories import (
    find_account_by_login,
    find_session_account,
    insert_session,
    revoke_session,
)
from olympiad_access.security import hash_token, normalize_login, verify_password

SESSION_TTL = timedelta(days=7)


@dataclass(frozen=True)
class IssuedSession:
    """Однократно выдаваемый токен и срок его действия."""

    access_token: str
    expires_at: datetime


async def login(db: AsyncSession, login: str, password: str) -> IssuedSession:
    """Проверяет пароль и создаёт независимую сессию."""
    try:
        normalized_login = normalize_login(login)
    except InvalidAccountData as error:
        raise InvalidCredentials() from error

    async with db.begin():
        account = await find_account_by_login(db, normalized_login)
        account_id = account.id if account else None
        stored_hash = account.password_hash if account else None

    if not await verify_password(password, stored_hash) or account_id is None:
        raise InvalidCredentials()

    token = token_urlsafe(32)
    now = datetime.now(UTC)
    expires_at = now + SESSION_TTL
    async with db.begin():
        await insert_session(db, account_id, hash_token(token), now, expires_at)
    return IssuedSession(token, expires_at)


async def logout(db: AsyncSession, token: str) -> None:
    """Отзывает только сессию, которой принадлежит переданный токен."""
    async with db.begin():
        if not await revoke_session(db, hash_token(token), datetime.now(UTC)):
            raise InvalidCredentials()


@dataclass(frozen=True)
class Principal:
    """Аккаунт и его актуальная роль для действующей сессии."""

    account_id: UUID
    role: RoleCode


async def get_principal(db: AsyncSession, token: str) -> Principal | None:
    """Ищет действующую сессию и читает роль из аккаунта."""
    account = await find_session_account(db, hash_token(token), datetime.now(UTC))
    if account is None:
        return None
    account_id, code = account
    return Principal(account_id, RoleCode(code))
