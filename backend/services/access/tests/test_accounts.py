import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_only_admin_can_create_accounts(
    client: AsyncClient, admin_headers: dict[str, str], role_ids: dict[str, int]
) -> None:
    body = {"login": " Task.Author ", "password": "author-pass", "role_id": role_ids["author"]}
    assert (await client.post("/accounts", json=body)).status_code == 401

    created = await client.post("/accounts", json=body, headers=admin_headers)
    assert created.status_code == 201
    assert created.json()["login"] == "task.author"
    assert created.json()["role_id"] == role_ids["author"]
    assert "password" not in created.json()
    assert (await client.post("/accounts", json=body, headers=admin_headers)).status_code == 409

    author = await client.post(
        "/auth/login", json={"login": "task.author", "password": "author-pass"}
    )
    assert author.status_code == 200
    author_headers = {"Authorization": f"Bearer {author.json()['access_token']}"}
    assert (await client.post("/accounts", json=body, headers=author_headers)).status_code == 403
    assert (await client.get("/roles", headers=author_headers)).status_code == 403

    another_admin = await client.post(
        "/accounts",
        json={
            "login": "another.admin",
            "password": "another-admin-pass",
            "role_id": role_ids["admin"],
        },
        headers=admin_headers,
    )
    assert another_admin.status_code == 201


@pytest.mark.asyncio
async def test_role_changes_apply_to_existing_sessions(
    client: AsyncClient, admin_headers: dict[str, str], role_ids: dict[str, int]
) -> None:
    credentials = {"login": "review.account", "password": "review-pass"}
    created = await client.post(
        "/accounts", json={**credentials, "role_id": role_ids["reviewer"]}, headers=admin_headers
    )
    assert created.status_code == 201
    account_id = created.json()["id"]
    logged_in = await client.post("/auth/login", json=credentials)
    session = {"Authorization": f"Bearer {logged_in.json()['access_token']}"}
    path = f"/accounts/{account_id}/role"
    assert (
        await client.patch(path, json={"role_id": role_ids["admin"]}, headers=session)
    ).status_code == 403

    changed = await client.patch(path, json={"role_id": role_ids["admin"]}, headers=admin_headers)
    assert changed.status_code == 200
    assert changed.json()["role_id"] == role_ids["admin"]

    new_account = {
        "login": "new.author",
        "password": "new-author-pass",
        "role_id": role_ids["author"],
    }
    assert (await client.post("/accounts", json=new_account, headers=session)).status_code == 201


@pytest.mark.parametrize(
    ("login", "password"),
    [
        (".invalid", "author-pass"),
        ("ab", "author-pass"),
        ("valid.login", "1234567"),
        ("valid.login", "я" * 37),
    ],
)
@pytest.mark.asyncio
async def test_rejects_invalid_credentials_when_creating_account(
    client: AsyncClient,
    admin_headers: dict[str, str],
    role_ids: dict[str, int],
    login: str,
    password: str,
) -> None:
    response = await client.post(
        "/accounts",
        json={"login": login, "password": password, "role_id": role_ids["author"]},
        headers=admin_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_keeps_spaces_in_eight_character_password(
    client: AsyncClient, admin_headers: dict[str, str], role_ids: dict[str, int]
) -> None:
    credentials = {"login": "space.author", "password": " пароль "}
    created = await client.post(
        "/accounts", json={**credentials, "role_id": role_ids["author"]}, headers=admin_headers
    )
    assert created.status_code == 201
    assert (await client.post("/auth/login", json=credentials)).status_code == 200
    wrong = {**credentials, "password": credentials["password"].strip()}
    assert (await client.post("/auth/login", json=wrong)).status_code == 401


@pytest.mark.asyncio
async def test_create_rejects_unknown_or_string_role_id(
    client: AsyncClient, admin_headers: dict[str, str], role_ids: dict[str, int]
) -> None:
    credentials = {"login": "test.account", "password": "test-password"}
    absent_role = max(role_ids.values()) + 1
    for role_id in (absent_role, str(role_ids["author"])):
        response = await client.post(
            "/accounts", json={**credentials, "role_id": role_id}, headers=admin_headers
        )
        assert response.status_code == 422
