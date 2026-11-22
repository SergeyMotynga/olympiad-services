"""Переменные окружения для подключения к PostgreSQL."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from sqlalchemy.engine import URL, make_url


class Settings(BaseSettings):
    """Принимает адрес целиком или параметры подключения из Compose."""

    database_url: SecretStr | None = None
    database_host: str = "postgres"
    database_port: int = 5432
    database_name: str | None = None
    database_user: str | None = None
    database_password: SecretStr | None = None

    @property
    def connection_url(self) -> URL:
        """Собирает адрес и сохраняет специальные символы в пароле."""
        if self.database_url is not None:
            return make_url(self.database_url.get_secret_value())
        if not (self.database_name and self.database_user and self.database_password):
            raise ValueError(
                "Задай DATABASE_URL или параметры DATABASE_NAME, DATABASE_USER и DATABASE_PASSWORD."
            )
        return URL.create(
            "postgresql+asyncpg",
            username=self.database_user,
            password=self.database_password.get_secret_value(),
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
        )
