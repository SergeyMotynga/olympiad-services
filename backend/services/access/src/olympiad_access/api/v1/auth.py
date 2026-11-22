"""Маршруты входа и выхода."""

from fastapi import APIRouter, Response

from olympiad_access.api.deps import Database, Token
from olympiad_access.api.errors import unauthorized
from olympiad_access.exceptions.access import InvalidCredentials
from olympiad_access.schemas.auth import Credentials, TokenResponse
from olympiad_access.services.auth import login, logout

router = APIRouter(prefix="/auth", tags=["Сессии"])


@router.post("/login")
async def login_route(body: Credentials, db: Database) -> TokenResponse:
    """Проверяет логин и пароль и выдаёт токен новой сессии."""
    try:
        session = await login(db, body.login, body.password.get_secret_value())
    except InvalidCredentials as error:
        raise unauthorized("Неверный логин или пароль.") from error
    return TokenResponse(access_token=session.access_token, expires_at=session.expires_at)


@router.post("/logout", status_code=204)
async def logout_route(db: Database, token: Token) -> Response:
    """Завершает сессию указанного токена."""
    try:
        await logout(db, token)
    except InvalidCredentials as error:
        raise unauthorized("Сессия недействительна.") from error
    return Response(status_code=204)
