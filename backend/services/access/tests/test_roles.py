import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_can_read_role_ids(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    assert (await client.get("/roles")).status_code == 401
    response = await client.get("/roles", headers=admin_headers)
    assert response.status_code == 200
    roles = response.json()
    assert {role["code"] for role in roles} == {"admin", "author", "representative", "reviewer"}
    assert all(isinstance(role["id"], int) and role["name"] for role in roles)
