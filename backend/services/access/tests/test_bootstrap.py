import os
import subprocess
import sys
from asyncio import to_thread
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from time import monotonic, sleep

import pytest
from httpx import AsyncClient
from sqlalchemy import Engine, text

from olympiad_access import bootstrap


def run_bootstrap(database_url: str, login: str) -> subprocess.CompletedProcess[str]:
    """Запускает команду bootstrap с тестовым паролем."""
    command = [
        sys.executable,
        "-m",
        "olympiad_access.bootstrap",
        "--password-stdin",
        "--login",
        login,
    ]
    env = {**os.environ, "DATABASE_URL": database_url, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        command,
        env=env,
        input="bootstrap-test-pass\n",
        encoding="utf-8",
        capture_output=True,
        check=False,
        timeout=45,
    )


def test_bootstrap_creates_only_the_first_admin(empty_accounts: None, database_url: str) -> None:
    first = run_bootstrap(database_url, "First.Admin")
    second = run_bootstrap(database_url, "Second.Admin")

    assert first.returncode == 0, first.stderr
    assert second.returncode == 1
    assert second.stderr.strip() == "Аккаунт администратора уже существует."


def test_concurrent_bootstrap_creates_only_one_admin(
    empty_accounts: None, database_url: str, test_database: Engine
) -> None:
    waiting_connections = text(
        "SELECT count(*) FROM pg_stat_activity "
        "WHERE datname = current_database() AND usename = current_user AND wait_event_type = 'Lock'"
    )
    with ThreadPoolExecutor(max_workers=2) as workers, test_database.connect() as observer:
        with test_database.begin() as gate:
            gate.execute(text("SELECT id FROM roles WHERE code = 'admin' FOR UPDATE"))
            attempts = [
                workers.submit(run_bootstrap, database_url, login)
                for login in ("First.Admin", "Second.Admin")
            ]

            # Снимаем блокировку, когда оба процесса дошли до конкурирующих транзакций.
            deadline = monotonic() + 20
            while monotonic() < deadline and not any(attempt.done() for attempt in attempts):
                with observer.begin():
                    if observer.scalar(waiting_connections) == len(attempts):
                        break
                sleep(0.05)
            else:
                pytest.fail("Оба процесса bootstrap должны ожидать блокировку одновременно.")

        results = [attempt.result() for attempt in attempts]

    assert sorted(result.returncode for result in results) == [0, 1], results
    rejected = next(result for result in results if result.returncode == 1)
    assert rejected.stderr.strip() == "Аккаунт администратора уже существует."


@pytest.mark.asyncio
async def test_bootstrap_accepts_crlf_on_stdin(
    client: AsyncClient, empty_accounts: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    login, password = "windows.admin", "  windows-password  "
    with monkeypatch.context() as cli:
        cli.setattr(sys, "argv", ["bootstrap", "--login", login, "--password-stdin"])
        cli.setattr(sys, "stdin", StringIO(password + "\r\n", newline="\n"))
        await to_thread(bootstrap.main)

    response = await client.post("/auth/login", json={"login": login, "password": password})

    assert response.status_code == 200
