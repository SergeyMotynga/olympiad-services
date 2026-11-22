"""HTTP API сервиса доступа."""

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, SecretStr
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from olympiad_access.domain import (
    AccessError,
    AccountNotFound,
    DuplicateLogin,
    Forbidden,
    InvalidAccountData,
    InvalidCredentials,
    RoleCode,
)
from olympiad_access.services.accounts import change_role, create_account
from olympiad_access.services.auth import login, logout

router = APIRouter()
bearer = HTTPBearer(auto_error=False)


async def open_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Открывает сессию PostgreSQL для запроса."""
    engine: AsyncEngine = request.app.state.database
    async with AsyncSession(engine, expire_on_commit=False) as db:
        yield db


Database = Annotated[AsyncSession, Depends(open_session)]


def require_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    """Извлекает токен сессии из заголовка Authorization."""
    if credentials is None:
        raise unauthorized("Требуется токен сессии.")
    return credentials.credentials


Token = Annotated[str, Depends(require_token)]


def unauthorized(message: str) -> HTTPException:
    return HTTPException(401, message, headers={"WWW-Authenticate": "Bearer"})


class Credentials(BaseModel):
    login: str
    password: SecretStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime


@router.post("/auth/login", tags=["Сессии"])
async def login_route(body: Credentials, db: Database) -> TokenResponse:
    """Проверяет логин и пароль и выдаёт токен новой сессии."""
    try:
        session = await login(db, body.login, body.password.get_secret_value())
    except InvalidCredentials as error:
        raise unauthorized("Неверный логин или пароль.") from error
    return TokenResponse(access_token=session.access_token, expires_at=session.expires_at)


@router.post("/auth/logout", tags=["Сессии"], status_code=204)
async def logout_route(db: Database, token: Token) -> Response:
    """Завершает сессию указанного токена."""
    try:
        await logout(db, token)
    except InvalidCredentials as error:
        raise unauthorized("Сессия недействительна.") from error
    return Response(status_code=204)


class NewAccount(Credentials):
    role: RoleCode


class AccountResponse(BaseModel):
    id: UUID
    login: str
    role: RoleCode


def account_error(error: AccessError) -> HTTPException:
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


@router.post("/accounts", tags=["Аккаунты"], status_code=201)
async def create_account_route(body: NewAccount, db: Database, token: Token) -> AccountResponse:
    """Создаёт аккаунт от имени администратора."""
    try:
        account = await create_account(
            db, token, body.login, body.password.get_secret_value(), body.role
        )
    except AccessError as error:
        raise account_error(error) from error
    return AccountResponse(id=account.id, login=account.login, role=body.role)


class RoleChange(BaseModel):
    role: RoleCode


@router.patch("/accounts/{account_id}/role", tags=["Аккаунты"])
async def change_role_route(
    account_id: UUID, body: RoleChange, db: Database, token: Token
) -> AccountResponse:
    """Меняет роль выбранного аккаунта от имени администратора."""
    try:
        account = await change_role(db, token, account_id, body.role)
    except AccessError as error:
        raise account_error(error) from error
    return AccountResponse(id=account.id, login=account.login, role=body.role)
