"""Зависимости HTTP-маршрутов."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from olympiad_access.api.errors import unauthorized
from olympiad_access.services.accounts import AccountService
from olympiad_access.services.auth import AuthService
from olympiad_access.services.roles import RoleService

bearer = HTTPBearer(auto_error=False)
SESSION_COOKIE = "olympiad_session"


def is_cabinet_request(request: Request) -> bool:
    """Запросы кабинета с cookie требуют заголовок, недоступный обычной форме."""
    return request.headers.get("X-Olympiad-Cabinet") == "1"


async def open_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Открывает сессию PostgreSQL для запроса."""
    engine: AsyncEngine = request.app.state.database
    async with AsyncSession(engine, expire_on_commit=False) as db:
        yield db


def require_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    """Извлекает токен сессии из Authorization."""
    if credentials is None:
        raise unauthorized("Требуется токен сессии.")
    return credentials.credentials


Database = Annotated[AsyncSession, Depends(open_session)]


def request_token(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    """Читает Bearer или сессию защищённого запроса кабинета."""
    if credentials is None and is_cabinet_request(request):
        token = request.cookies.get(SESSION_COOKIE)
        if token:
            return token
    return require_token(credentials)


Token = Annotated[str, Depends(request_token)]


def get_auth_service(db: Database) -> AuthService:
    """Создаёт сервис сессий для запроса."""
    return AuthService(db)


def get_account_service(db: Database) -> AccountService:
    """Создаёт сервис управления аккаунтами для запроса."""
    return AccountService(db)


def get_role_service(db: Database) -> RoleService:
    """Создаёт сервис справочника для запроса."""
    return RoleService(db)


Auth = Annotated[AuthService, Depends(get_auth_service)]
Accounts = Annotated[AccountService, Depends(get_account_service)]
Roles = Annotated[RoleService, Depends(get_role_service)]
