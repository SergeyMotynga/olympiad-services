"""Маршрут справочника ролей."""

from fastapi import APIRouter

from olympiad_access.api.deps import Database, Token
from olympiad_access.api.errors import account_error
from olympiad_access.exceptions.access import AccessError
from olympiad_access.schemas.roles import RoleResponse
from olympiad_access.services.roles import get_roles

router = APIRouter(tags=["Роли"])


@router.get("/roles")
async def list_roles_route(db: Database, token: Token) -> list[RoleResponse]:
    """Показывает администратору роли и их идентификаторы."""
    try:
        roles = await get_roles(db, token)
    except AccessError as error:
        raise account_error(error) from error
    return [RoleResponse.model_validate(role) for role in roles]
