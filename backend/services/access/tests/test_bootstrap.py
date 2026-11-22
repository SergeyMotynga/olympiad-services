import os
import subprocess
import sys
from asyncio import to_thread
from io import StringIO

import pytest
from httpx import AsyncClient

from olympiad_access import bootstrap


def test_bootstrap_creates_only_the_first_admin(empty_accounts: None, database_url: str) -> None:
    command = [
        sys.executable,
        "-m",
        "olympiad_access.bootstrap",
        "--password-stdin",
    ]
    env = {**os.environ, "DATABASE_URL": database_url, "PYTHONIOENCODING": "utf-8"}

    first = subprocess.run(
        [*command, "--login", "First.Admin"],
        env=env,
        input="first-admin-pass\n",
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    second = subprocess.run(
        [*command, "--login", "Second.Admin"],
        env=env,
        input="second-admin-pass\n",
        encoding="utf-8",
        capture_output=True,
        check=False,
    )

    assert first.returncode == 0, first.stderr
    assert second.returncode == 1
    assert second.stderr.strip() == "Аккаунт администратора уже существует."


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
