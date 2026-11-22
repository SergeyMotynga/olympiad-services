"""Схемы HTTP для входа и сессий."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, SecretStr


class Credentials(BaseModel):
    login: str
    password: SecretStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
