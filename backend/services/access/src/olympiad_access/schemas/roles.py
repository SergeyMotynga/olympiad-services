"""Схема записи справочника ролей в HTTP API."""

from pydantic import BaseModel, ConfigDict

from olympiad_access.domain.roles import RoleCode


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: RoleCode
    name: str
