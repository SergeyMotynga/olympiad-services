"""Правила логинов и паролей при создании аккаунта."""

from re import compile

from olympiad_access.exceptions.access import InvalidAccountData

MAX_PASSWORD_BYTES = 72
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


def validate_password(password: str) -> bytes:
    """Проверяет пароль и кодирует его без изменений."""
    try:
        encoded = password.encode("utf-8")
    except UnicodeError as error:
        raise InvalidAccountData("Пароль должен быть строкой в UTF-8.") from error
    if len(password) < 8 or len(encoded) > MAX_PASSWORD_BYTES:
        raise InvalidAccountData("Нужно от 8 символов до 72 байт в UTF-8.")
    return encoded
