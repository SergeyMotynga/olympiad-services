from socket import AF_INET, SOCK_STREAM, socket

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from olympiad_access.main import app as access_app
from olympiad_submissions.main import app as submissions_app
from olympiad_tasks_print.main import app as tasks_print_app


@pytest.mark.parametrize("app", [access_app, tasks_print_app, submissions_app])
@pytest.mark.asyncio
async def test_reports_not_ready_when_database_is_unavailable(
    app: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with socket(AF_INET, SOCK_STREAM) as unavailable_database:
        unavailable_database.bind(("127.0.0.1", 0))
        port = unavailable_database.getsockname()[1]
        monkeypatch.setenv(
            "DATABASE_URL", f"postgresql+asyncpg://test:test@127.0.0.1:{port}/access"
        )

        async with (
            app.router.lifespan_context(app),
            AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client,
        ):
            response = await client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
