"""Запросы к аккаунтам."""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from olympiad_access.models.accounts import Account


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


async def update_role(db: AsyncSession, account_id: UUID, value: int) -> Account | None:
    """Назначает роль существующему аккаунту."""
    query = update(Account).where(Account.id == account_id).values(role_id=value).returning(Account)
    return (await db.execute(query)).scalar_one_or_none()
