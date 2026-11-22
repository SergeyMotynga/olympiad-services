import os
import subprocess
import sys


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
