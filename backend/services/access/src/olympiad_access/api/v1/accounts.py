"""Маршруты управления аккаунтами."""

from uuid import UUID

from fastapi import APIRouter

from olympiad_access.api.deps import Database, Token
from olympiad_access.api.errors import account_error
from olympiad_access.exceptions.access import AccessError
from olympiad_access.schemas.accounts import AccountResponse, NewAccount, RoleChange
from olympiad_access.services.accounts import change_role, create_account

router = APIRouter(prefix="/accounts", tags=["Аккаунты"])


@router.post("", status_code=201)
async def create_account_route(body: NewAccount, db: Database, token: Token) -> AccountResponse:
    """Создаёт аккаунт с ролью из справочника."""
    try:
        account = await create_account(
            db, token, body.login, body.password.get_secret_value(), body.role_id
        )
    except AccessError as error:
        raise account_error(error) from error
    return AccountResponse.model_validate(account)


@router.patch("/{account_id}/role")
async def change_role_route(
    account_id: UUID, body: RoleChange, db: Database, token: Token
) -> AccountResponse:
    """Меняет роль выбранного аккаунта от имени администратора."""
    try:
        account = await change_role(db, token, account_id, body.role_id)
    except AccessError as error:
        raise account_error(error) from error
    return AccountResponse.model_validate(account)
