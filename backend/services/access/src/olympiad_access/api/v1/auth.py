"""Маршруты входа, выхода и текущей сессии."""

from fastapi import APIRouter, HTTPException, Request, Response

from olympiad_access.api.deps import SESSION_COOKIE, Auth, Token, is_cabinet_request
from olympiad_access.api.errors import unauthorized
from olympiad_access.domain.permissions import LIST_ROLES
from olympiad_access.exceptions.access import InvalidCredentials
from olympiad_access.schemas.auth import Credentials, CurrentAccountResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Сессии"])
page_router = APIRouter(prefix="/internal/page-access", include_in_schema=False)


@page_router.get("/accounts", status_code=204)
async def accounts_page_access(request: Request, service: Auth) -> Response:
    """Проверяет доступ по сессии перед выдачей HTML страницы аккаунтов."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise unauthorized("Требуется токен сессии.")
    try:
        account = await service.current_account(token)
    except InvalidCredentials as error:
        raise unauthorized("Сессия недействительна.") from error
    if LIST_ROLES not in account.operations:
        raise HTTPException(403)
    return Response(status_code=204)


@router.get("/me")
async def current_account_route(
    service: Auth, token: Token, response: Response
) -> CurrentAccountResponse:
    """Возвращает текущий аккаунт и доступные операции."""
    try:
        account = await service.current_account(token)
    except InvalidCredentials as error:
        raise unauthorized("Сессия недействительна.") from error
    response.headers["Cache-Control"] = "no-store"
    return CurrentAccountResponse(
        account_id=account.account_id,
        login=account.login,
        expires_at=account.expires_at,
        operations=account.operations,
    )


@router.post("/login")
async def login_route(
    body: Credentials, service: Auth, request: Request, response: Response
) -> TokenResponse:
    """Проверяет логин и пароль и выдаёт токен новой сессии."""
    try:
        session = await service.login(body.login, body.password.get_secret_value())
    except InvalidCredentials as error:
        raise unauthorized("Неверный логин или пароль.") from error
    if is_cabinet_request(request):
        response.set_cookie(
            SESSION_COOKIE,
            session.access_token,
            expires=session.expires_at,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
        )
    response.headers["Cache-Control"] = "no-store"
    return TokenResponse(access_token=session.access_token, expires_at=session.expires_at)


@router.post("/logout", status_code=204)
async def logout_route(service: Auth, token: Token, request: Request) -> Response:
    """Завершает сессию указанного токена."""
    try:
        await service.logout(token)
    except InvalidCredentials as error:
        raise unauthorized("Сессия недействительна.") from error
    response = Response(status_code=204)
    if request.cookies.get(SESSION_COOKIE) == token:
        response.delete_cookie(SESSION_COOKIE, httponly=True, secure=request.url.scheme == "https")
    return response
