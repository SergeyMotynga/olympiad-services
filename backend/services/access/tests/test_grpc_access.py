from asyncio import CancelledError
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import grpc
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from olympiad_access.api.grpc import serve_access
from olympiad_contracts.access_pb2 import CheckAccessRequest
from olympiad_contracts.access_pb2_grpc import AccessServiceStub
from olympiad_runtime.repositories.database import build_engine


@pytest.mark.asyncio
@pytest.mark.parametrize("startup_error", [RuntimeError, CancelledError])
async def test_grpc_server_stops_when_startup_fails(startup_error: type[BaseException]) -> None:
    server = MagicMock(spec=grpc.aio.Server)
    server.start.side_effect = startup_error
    engine = MagicMock(spec=AsyncEngine)

    with patch("grpc.aio.server", return_value=server), pytest.raises(startup_error):
        async with serve_access(engine, "127.0.0.1:0"):
            pytest.fail("Сервер не должен перейти к приёму запросов после сбоя запуска.")

    server.stop.assert_awaited_once()


@pytest_asyncio.fixture
async def access_stub(database_url: str) -> AsyncIterator[AccessServiceStub]:
    """Поднимает gRPC-сервер и открывает клиент для теста."""
    engine = build_engine(database_url)
    try:
        async with (
            serve_access(engine, "127.0.0.1:0") as port,
            grpc.aio.insecure_channel(f"127.0.0.1:{port}") as channel,
        ):
            yield AccessServiceStub(channel)  # type: ignore[no-untyped-call]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_check_access_uses_current_role(
    client: AsyncClient,
    admin_headers: dict[str, str],
    role_ids: dict[str, int],
    access_stub: AccessServiceStub,
) -> None:
    credentials = {"login": "print.author", "password": "author-pass"}
    created = await client.post(
        "/accounts", json={**credentials, "role_id": role_ids["author"]}, headers=admin_headers
    )
    assert created.status_code == 201
    account_id = created.json()["id"]
    signed_in = await client.post("/auth/login", json=credentials)
    token = signed_in.json()["access_token"]
    request = CheckAccessRequest(session_token=token, operation="tasks:create")

    reply = await access_stub.CheckAccess(request, timeout=5)
    assert reply.allowed
    assert reply.account_id == account_id

    changed = await client.patch(
        f"/accounts/{account_id}/role",
        json={"role_id": role_ids["representative"]},
        headers=admin_headers,
    )
    assert changed.status_code == 200
    reply = await access_stub.CheckAccess(request, timeout=5)
    assert not reply.allowed
    assert not reply.account_id

    allowed_request = CheckAccessRequest(session_token=token, operation="submissions:create")
    assert (await access_stub.CheckAccess(allowed_request, timeout=5)).allowed
    assert (
        await client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    ).status_code == 204
    assert not (await access_stub.CheckAccess(allowed_request, timeout=5)).allowed


@pytest.mark.asyncio
async def test_check_access_rejects_session_at_expiration(
    client: AsyncClient, admin_account: tuple[str, str], access_stub: AccessServiceStub
) -> None:
    login, password = admin_account
    response = await client.post("/auth/login", json={"login": login, "password": password})
    assert response.status_code == 200
    session = response.json()
    expires_at = datetime.fromisoformat(session["expires_at"])
    request = CheckAccessRequest(session_token=session["access_token"], operation="tasks:print")

    with patch("olympiad_access.services.auth.datetime", wraps=datetime) as clock:
        clock.now.return_value = expires_at - timedelta(microseconds=1)
        assert (await access_stub.CheckAccess(request, timeout=5)).allowed

        clock.now.return_value = expires_at
        reply = await access_stub.CheckAccess(request, timeout=5)
        assert not reply.allowed
        assert not reply.account_id
