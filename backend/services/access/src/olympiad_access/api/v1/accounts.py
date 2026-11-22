"""Маршруты управления аккаунтами."""

from uuid import UUID

from fastapi import APIRouter

from olympiad_access.api.deps import Accounts, Token
from olympiad_access.api.errors import account_error
from olympiad_access.api.routes import ProtectedWriteRoute
from olympiad_access.domain.permissions import CHANGE_ACCOUNT_ROLE, CREATE_ACCOUNT
from olympiad_access.exceptions.access import AccessError
from olympiad_access.schemas.accounts import AccountResponse, NewAccount, RoleChange

router = APIRouter(prefix="/accounts", tags=["Аккаунты"], route_class=ProtectedWriteRoute)


@router.post("", status_code=201, name=CREATE_ACCOUNT)
async def create_account_route(
    body: NewAccount, service: Accounts, token: Token
) -> AccountResponse:
    """Создаёт аккаунт с ролью из справочника."""
    try:
        account = await service.create_account(
            token, body.login, body.password.get_secret_value(), body.role_id
        )
    except AccessError as error:
        raise account_error(error) from error
    return AccountResponse.model_validate(account)


@router.patch("/{account_id}/role", name=CHANGE_ACCOUNT_ROLE)
async def change_role_route(
    account_id: UUID, body: RoleChange, service: Accounts, token: Token
) -> AccountResponse:
    """Меняет роль выбранного аккаунта от имени администратора."""
    try:
        account = await service.change_role(token, account_id, body.role_id)
    except AccessError as error:
        raise account_error(error) from error
    return AccountResponse.model_validate(account)
