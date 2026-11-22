"""Общие метаданные ORM-моделей сервиса доступа."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Декларативная основа таблиц сервиса доступа."""
