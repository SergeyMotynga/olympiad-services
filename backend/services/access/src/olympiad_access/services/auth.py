"""Вход и хранение сессий."""

from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

from sqlalchemy.ext.asyncio import AsyncSession

from olympiad_access.core.security import hash_token, verify_password
from olympiad_access.domain.roles import RoleCode
from olympiad_access.dto.auth import IssuedSession, Principal
from olympiad_access.exceptions.access import InvalidAccountData, InvalidCredentials
from olympiad_access.repositories.accounts import find_account_by_login
from olympiad_access.repositories.sessions import (
    find_session_account,
    insert_session,
    revoke_session,
)
from olympiad_access.validators.credentials import normalize_login

SESSION_TTL = timedelta(days=7)


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


async def get_principal(db: AsyncSession, token: str) -> Principal | None:
    """Ищет действующую сессию и читает роль из аккаунта."""
    account = await find_session_account(db, hash_token(token), datetime.now(UTC))
    if account is None:
        return None
    account_id, code = account
    return Principal(account_id, RoleCode(code))
