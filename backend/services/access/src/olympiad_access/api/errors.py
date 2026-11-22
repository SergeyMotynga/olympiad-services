"""Ответы HTTP для ошибок сервиса доступа."""

from fastapi import HTTPException

from olympiad_access.exceptions.access import (
    AccessError,
    AccountNotFound,
    DuplicateLogin,
    Forbidden,
    InvalidAccountData,
    InvalidCredentials,
)


def unauthorized(message: str) -> HTTPException:
    """Возвращает ответ с предложением авторизоваться."""
    return HTTPException(401, message, headers={"WWW-Authenticate": "Bearer"})


def account_error(error: AccessError) -> HTTPException:
    """Преобразует ошибку работы с аккаунтом или ролью в ответ HTTP."""
    if isinstance(error, InvalidCredentials):
        return unauthorized("Сессия недействительна.")
    if isinstance(error, Forbidden):
        return HTTPException(403, str(error))
    if isinstance(error, AccountNotFound):
        return HTTPException(404, str(error))
    if isinstance(error, DuplicateLogin):
        return HTTPException(409, str(error))
    if isinstance(error, InvalidAccountData):
        return HTTPException(422, str(error))
    raise error
