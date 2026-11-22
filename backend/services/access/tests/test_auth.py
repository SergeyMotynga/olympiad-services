from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_creates_an_independent_week_long_session(
    client: AsyncClient, admin_account: tuple[str, str]
) -> None:
    login, password = admin_account
    before = datetime.now(UTC)
    first = await client.post(
        "/auth/login", json={"login": f" {login.upper()} ", "password": password}
    )
    second = await client.post("/auth/login", json={"login": login, "password": password})

    assert first.status_code == second.status_code == 200
    assert first.json()["access_token"] != second.json()["access_token"]
    assert first.json()["token_type"] == "bearer"
    expires_at = datetime.fromisoformat(first.json()["expires_at"])
    assert before + timedelta(days=7) <= expires_at <= datetime.now(UTC) + timedelta(days=7)


@pytest.mark.asyncio
async def test_logout_revokes_only_the_current_session(
    client: AsyncClient, admin_account: tuple[str, str]
) -> None:
    credentials = dict(zip(("login", "password"), admin_account, strict=True))
    first = (await client.post("/auth/login", json=credentials)).json()["access_token"]
    second = (await client.post("/auth/login", json=credentials)).json()["access_token"]
    first_headers = {"Authorization": f"Bearer {first}"}

    assert (await client.post("/auth/logout", headers=first_headers)).status_code == 204
    assert (await client.post("/auth/logout", headers=first_headers)).status_code == 401
    assert (
        await client.post("/auth/logout", headers={"Authorization": f"Bearer {second}"})
    ).status_code == 204


@pytest.mark.asyncio
async def test_wrong_password_and_missing_login_have_same_error(
    client: AsyncClient, admin_account: tuple[str, str]
) -> None:
    login, _ = admin_account
    wrong_password = await client.post(
        "/auth/login", json={"login": login, "password": "wrong-password"}
    )
    missing_login = await client.post(
        "/auth/login", json={"login": "missing.login", "password": "wrong-password"}
    )

    assert wrong_password.status_code == missing_login.status_code == 401
    assert wrong_password.json() == missing_login.json()
    assert wrong_password.headers["www-authenticate"] == "Bearer"
