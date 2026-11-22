"""Чтение и запись данных сервиса доступа."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from olympiad_access.domain import RoleCode
from olympiad_access.models import Account, Role, Session


async def role_id(db: AsyncSession, code: RoleCode, *, lock: bool = False) -> int:
    """Находит роль, созданную миграцией."""
    query = select(Role.id).where(Role.code == code)
    if lock:
        query = query.with_for_update()
    return (await db.execute(query)).scalar_one()


async def role_is_assigned(db: AsyncSession, value: int) -> bool:
    """Проверяет наличие аккаунта с указанной ролью."""
    query = select(Account.id).where(Account.role_id == value).limit(1)
    return (await db.execute(query)).scalar_one_or_none() is not None


async def insert_account(
    db: AsyncSession, login: str, password_hash: str, assigned_role: int
) -> Account | None:
    """Добавляет аккаунт, если логин ещё свободен."""
    query = (
        insert(Account)
        .values(login=login, password_hash=password_hash, role_id=assigned_role)
        .on_conflict_do_nothing(index_elements=[Account.login])
        .returning(Account)
    )
    return (await db.execute(query)).scalar_one_or_none()


async def find_account_by_login(db: AsyncSession, login: str) -> Account | None:
    """Возвращает аккаунт с указанным нормализованным логином."""
    query = select(Account).where(Account.login == login)
    return (await db.execute(query)).scalar_one_or_none()


async def insert_session(
    db: AsyncSession,
    account_id: UUID,
    token_hash: bytes,
    created_at: datetime,
    expires_at: datetime,
) -> None:
    """Добавляет сессию в текущей транзакции."""
    db.add(
        Session(
            account_id=account_id,
            token_hash=token_hash,
            created_at=created_at,
            expires_at=expires_at,
        )
    )


def active_session(token_hash: bytes, now: datetime) -> tuple[ColumnElement[bool], ...]:
    """Ограничения для поиска действующей сессии."""
    return (
        Session.token_hash == token_hash,
        Session.revoked_at.is_(None),
        Session.expires_at > now,
    )


async def revoke_session(db: AsyncSession, token_hash: bytes, now: datetime) -> bool:
    """Отзывает одну действующую сессию."""
    query = (
        update(Session)
        .where(*active_session(token_hash, now))
        .values(revoked_at=now)
        .returning(Session.id)
    )
    return (await db.execute(query)).scalar_one_or_none() is not None


async def find_session_account(
    db: AsyncSession, token_hash: bytes, now: datetime
) -> tuple[UUID, str] | None:
    """Возвращает владельца действующей сессии и его текущую роль."""
    query = (
        select(Account.id, Role.code)
        .select_from(Session)
        .join(Account, Account.id == Session.account_id)
        .join(Role, Role.id == Account.role_id)
        .where(*active_session(token_hash, now))
    )
    row = (await db.execute(query)).one_or_none()
    return row._tuple() if row is not None else None


async def update_role(db: AsyncSession, account_id: UUID, value: int) -> Account | None:
    """Назначает роль существующему аккаунту."""
    query = update(Account).where(Account.id == account_id).values(role_id=value).returning(Account)
    return (await db.execute(query)).scalar_one_or_none()
