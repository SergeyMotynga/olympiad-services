"""Маршруты входа и выхода."""

from fastapi import APIRouter, Response

from olympiad_access.api.deps import Auth, Token
from olympiad_access.api.errors import unauthorized
from olympiad_access.exceptions.access import InvalidCredentials
from olympiad_access.schemas.auth import Credentials, TokenResponse

router = APIRouter(prefix="/auth", tags=["Сессии"])


@router.post("/login")
async def login_route(body: Credentials, service: Auth) -> TokenResponse:
    """Проверяет логин и пароль и выдаёт токен новой сессии."""
    try:
        session = await service.login(body.login, body.password.get_secret_value())
    except InvalidCredentials as error:
        raise unauthorized("Неверный логин или пароль.") from error
    return TokenResponse(access_token=session.access_token, expires_at=session.expires_at)


@router.post("/logout", status_code=204)
async def logout_route(service: Auth, token: Token) -> Response:
    """Завершает сессию указанного токена."""
    try:
        await service.logout(token)
    except InvalidCredentials as error:
        raise unauthorized("Сессия недействительна.") from error
    return Response(status_code=204)
