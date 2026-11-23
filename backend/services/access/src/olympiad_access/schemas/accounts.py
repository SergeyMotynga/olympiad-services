"""Схемы HTTP для управления аккаунтами."""

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from olympiad_access.schemas.auth import Credentials

RoleId = Annotated[int, Field(strict=True, ge=1, le=32767)]


class NewAccount(Credentials):
    role_id: RoleId


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    login: str
    role_id: RoleId


class RoleChange(BaseModel):
    role_id: RoleId
