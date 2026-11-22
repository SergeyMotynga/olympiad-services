"""Запросы к сессиям входа."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from olympiad_access.models.accounts import Account, Role, Session


def _active_session(token_hash: bytes, now: datetime) -> tuple[ColumnElement[bool], ...]:
    """Ограничения для поиска действующей сессии."""
    return (
        Session.token_hash == token_hash,
        Session.revoked_at.is_(None),
        Session.expires_at > now,
    )


class SessionRepository:
    """Запросы к сессиям входа."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def insert_session(
        self,
        account_id: UUID,
        token_hash: bytes,
        created_at: datetime,
        expires_at: datetime,
    ) -> None:
        """Добавляет сессию в текущей транзакции."""
        self.db.add(
            Session(
                account_id=account_id,
                token_hash=token_hash,
                created_at=created_at,
                expires_at=expires_at,
            )
        )

    async def revoke_session(self, token_hash: bytes, now: datetime) -> bool:
        """Отзывает одну действующую сессию."""
        query = (
            update(Session)
            .where(*_active_session(token_hash, now))
            .values(revoked_at=now)
            .returning(Session.id)
        )
        return (await self.db.execute(query)).scalar_one_or_none() is not None

    async def find_session_account(
        self, token_hash: bytes, now: datetime
    ) -> tuple[UUID, str] | None:
        """Возвращает владельца действующей сессии и его текущую роль."""
        query = (
            select(Account.id, Role.code)
            .select_from(Session)
            .join(Account, Account.id == Session.account_id)
            .join(Role, Role.id == Account.role_id)
            .where(*_active_session(token_hash, now))
        )
        row = (await self.db.execute(query)).one_or_none()
        return row._tuple() if row is not None else None
