import os
import subprocess
import sys
from collections.abc import AsyncIterator, Iterator
from os import getenv
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url

from olympiad_access.main import app

ACCESS_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def database_url() -> str:
    """Читает адрес отдельной базы тестов сервиса доступа."""
    value = getenv("ACCESS_TEST_DATABASE_URL")
    if not value:
        pytest.skip("Для тестов PostgreSQL задай ACCESS_TEST_DATABASE_URL.")
    url = make_url(value)
    if url.database != "access_test" or url.username != "access_test_app":
        pytest.fail("Тестам нужна отдельная база access_test с ролью access_test_app.")
    return value


@pytest.fixture(scope="session")
def test_database(database_url: str) -> Iterator[Engine]:
    """Применяет Alembic к тестовой базе."""
    engine = create_engine(make_url(database_url).set(drivername="postgresql+psycopg"))
    migration = Config(str(ACCESS_DIR / "alembic.ini"))
    migration.attributes["database_url"] = database_url
    command.upgrade(migration, "head")
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def empty_accounts(test_database: Engine) -> None:
    """Очищает записи между тестами в отдельной базе."""
    with test_database.begin() as db:
        db.execute(text("TRUNCATE sessions, accounts"))


@pytest.fixture
def admin_account(empty_accounts: None, database_url: str) -> tuple[str, str]:
    """Создаёт администратора той же командой, что и в Compose."""
    login, password = "first.admin", "admin-pass-for-test"
    subprocess.run(
        [sys.executable, "-m", "olympiad_access.bootstrap", "--login", login, "--password-stdin"],
        env={**os.environ, "DATABASE_URL": database_url},
        input=password + "\n",
        text=True,
        check=True,
    )
    return login, password


@pytest_asyncio.fixture
async def client(
    database_url: str, test_database: Engine, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[AsyncClient]:
    """Отправляет HTTP-запросы приложению с тестовой базой."""
    monkeypatch.setenv("DATABASE_URL", database_url)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http,
    ):
        yield http


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, admin_account: tuple[str, str]) -> dict[str, str]:
    """Получает заголовок авторизации через реальный вход."""
    login, password = admin_account
    response = await client.post("/auth/login", json={"login": login, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
