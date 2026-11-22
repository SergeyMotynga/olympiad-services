"""Проверка учётных данных и работа с хешами."""

from asyncio import to_thread
from hashlib import sha256
from re import compile

import bcrypt

from olympiad_access.domain import InvalidAccountData

LOGIN_PATTERN = compile(r"[a-zA-Z0-9][a-zA-Z0-9._-]{2,31}")


def normalize_login(login: str) -> str:
    """Проверяет формат логина и приводит его к нижнему регистру."""
    login = login.strip()
    if not LOGIN_PATTERN.fullmatch(login):
        raise InvalidAccountData(
            "Логин должен содержать от 3 до 32 латинских букв, цифр, точек, "
            "дефисов или подчёркиваний и начинаться с буквы или цифры."
        )
    return login.lower()


async def hash_password(password: str) -> str:
    """Проверяет пароль и сохраняет его без нормализации."""
    try:
        encoded = password.encode("utf-8")
    except UnicodeError as error:
        raise InvalidAccountData("Пароль должен быть строкой в UTF-8.") from error
    if len(password) < 8 or len(encoded) > 72:
        raise InvalidAccountData("Нужно от 8 символов до 72 байт в UTF-8.")
    hashed = await to_thread(bcrypt.hashpw, encoded, bcrypt.gensalt())
    return hashed.decode("ascii")


# Хеш случайной строки для проверки при отсутствующем аккаунте.
DUMMY_PASSWORD_HASH = b"$2b$12$rClgtfhvqU8Axyiwfsr9uOLaQIupaUL/SELCyNjBQ4cgvtW2cXh.S"


async def verify_password(password: str, password_hash: str | None) -> bool:
    """Проверяет пароль целиком. Отсутствующий аккаунт тоже проходит вычисление bcrypt."""
    try:
        encoded = password.encode("utf-8")
    except UnicodeError:
        return False
    if len(encoded) > 72:
        return False
    expected = password_hash.encode("ascii") if password_hash is not None else DUMMY_PASSWORD_HASH
    matches = await to_thread(bcrypt.checkpw, encoded, expected)
    return matches and password_hash is not None


def hash_token(token: str) -> bytes:
    """Возвращает SHA-256 случайного токена сессии."""
    return sha256(token.encode("utf-8")).digest()
