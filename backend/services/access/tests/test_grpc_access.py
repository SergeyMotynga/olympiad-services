import grpc
import pytest
from httpx import AsyncClient

from olympiad_access.grpc_server import serve_access
from olympiad_contracts.access_pb2 import CheckAccessRequest
from olympiad_contracts.access_pb2_grpc import AccessServiceStub
from olympiad_runtime.repositories.database import build_engine


@pytest.mark.asyncio
async def test_check_access_uses_current_role(
    client: AsyncClient, admin_headers: dict[str, str], database_url: str
) -> None:
    credentials = {"login": "print.author", "password": "author-pass"}
    created = await client.post(
        "/accounts", json={**credentials, "role": "author"}, headers=admin_headers
    )
    assert created.status_code == 201
    account_id = created.json()["id"]
    signed_in = await client.post("/auth/login", json=credentials)
    token = signed_in.json()["access_token"]
    request = CheckAccessRequest(session_token=token, operation="tasks:create")

    engine = build_engine(database_url)
    try:
        async with (
            serve_access(engine, "127.0.0.1:0") as port,
            grpc.aio.insecure_channel(f"127.0.0.1:{port}") as channel,
        ):
            stub = AccessServiceStub(channel)  # type: ignore[no-untyped-call]
            reply = await stub.CheckAccess(request, timeout=5)
            assert reply.allowed
            assert reply.account_id == account_id

            changed = await client.patch(
                f"/accounts/{account_id}/role",
                json={"role": "representative"},
                headers=admin_headers,
            )
            assert changed.status_code == 200
            reply = await stub.CheckAccess(request, timeout=5)
            assert not reply.allowed
            assert not reply.account_id

            allowed_request = CheckAccessRequest(
                session_token=token, operation="submissions:create"
            )
            assert (await stub.CheckAccess(allowed_request, timeout=5)).allowed
            assert (
                await client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
            ).status_code == 204
            assert not (await stub.CheckAccess(allowed_request, timeout=5)).allowed
    finally:
        await engine.dispose()
