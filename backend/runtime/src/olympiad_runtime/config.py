from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки подключения к базе приложения."""

    database_url: str
