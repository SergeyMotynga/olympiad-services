"""Ответы HTTP для ошибок сервиса доступа."""

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from olympiad_access.exceptions.access import (
    AccessError,
    AccountNotFound,
    DuplicateLogin,
    Forbidden,
    InvalidAccountData,
    InvalidCredentials,
)


async def request_validation_error(
    _request: Request, error: RequestValidationError
) -> JSONResponse:
    """Возвращает местоположение, тип и сообщение без входных данных."""
    detail = [
        {"loc": item["loc"], "type": item["type"], "msg": item["msg"]} for item in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detail})


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
