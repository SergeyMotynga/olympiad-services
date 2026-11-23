"""Результаты сценариев входа и проверки сессии."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from olympiad_access.domain.roles import RoleCode


@dataclass(frozen=True)
class IssuedSession:
    """Однократно выдаваемый токен и срок его действия."""

    access_token: str
    expires_at: datetime


@dataclass(frozen=True)
class Principal:
    """Аккаунт и его актуальная роль для действующей сессии."""

    account_id: UUID
    role: RoleCode
    login: str
    expires_at: datetime


@dataclass(frozen=True)
class CurrentAccount:
    """Аккаунт действующей сессии и доступные ему операции."""

    account_id: UUID
    login: str
    expires_at: datetime
    operations: tuple[str, ...]
