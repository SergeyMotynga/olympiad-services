"""Хеширование паролей и токенов сессий."""

from asyncio import to_thread
from hashlib import sha256

import bcrypt

from olympiad_access.validators.credentials import MAX_PASSWORD_BYTES


async def hash_password(password: bytes) -> str:
    """Хеширует проверенный пароль."""
    hashed = await to_thread(bcrypt.hashpw, password, bcrypt.gensalt())
    return hashed.decode("ascii")


# Хеш случайной строки для проверки при отсутствующем аккаунте.
DUMMY_PASSWORD_HASH = b"$2b$12$rClgtfhvqU8Axyiwfsr9uOLaQIupaUL/SELCyNjBQ4cgvtW2cXh.S"


async def verify_password(password: str, password_hash: str | None) -> bool:
    """Проверяет пароль целиком. Отсутствующий аккаунт тоже проходит вычисление bcrypt."""
    try:
        encoded = password.encode("utf-8")
    except UnicodeError:
        return False
    if len(encoded) > MAX_PASSWORD_BYTES:
        return False
    expected = password_hash.encode("ascii") if password_hash is not None else DUMMY_PASSWORD_HASH
    matches = await to_thread(bcrypt.checkpw, encoded, expected)
    return matches and password_hash is not None


def hash_token(token: str) -> bytes:
    """Возвращает SHA-256 случайного токена сессии."""
    return sha256(token.encode("utf-8")).digest()
