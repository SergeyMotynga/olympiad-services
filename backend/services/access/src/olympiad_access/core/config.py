"""Настройки внутреннего gRPC-интерфейса."""

from pydantic_settings import BaseSettings


class AccessSettings(BaseSettings):
    """Адрес прослушивания внутри окружения запуска."""

    access_grpc_address: str | None = None
