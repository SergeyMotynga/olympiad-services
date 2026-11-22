"""Таблицы ролей и аккаунтов."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Identity,
    LargeBinary,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Метаданные таблиц сервиса доступа."""


class Role(Base):
    """Запись справочника ролей."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(SmallInteger(), Identity(), primary_key=True)
    code: Mapped[str] = mapped_column(Text(), unique=True)
    name: Mapped[str] = mapped_column(Text())


class Account(Base):
    """Аккаунт с уникальным логином и одной ролью."""

    __tablename__ = "accounts"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    login: Mapped[str] = mapped_column(String(32), unique=True)
    password_hash: Mapped[str] = mapped_column(Text())
    role_id: Mapped[int] = mapped_column(SmallInteger(), ForeignKey("roles.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Session(Base):
    """Сессия конкретного входа в аккаунт."""

    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    token_hash: Mapped[bytes] = mapped_column(LargeBinary(), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
