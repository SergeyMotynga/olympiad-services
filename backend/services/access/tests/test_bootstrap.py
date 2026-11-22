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
        "--login",
        "First.Admin",
        "--password-stdin",
    ]
    env = {**os.environ, "DATABASE_URL": database_url}

    first = subprocess.run(command, env=env, input="first-admin-pass\n", text=True, check=False)
    second = subprocess.run(command, env=env, input="second-admin-pass\n", text=True, check=False)

    assert first.returncode == 0
    assert second.returncode != 0


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
