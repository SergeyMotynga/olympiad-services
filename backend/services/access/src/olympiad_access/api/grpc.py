"""Внутренний gRPC-интерфейс сервиса доступа."""

from asyncio import timeout
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import grpc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from olympiad_access.services.access import check_access
from olympiad_contracts.access_pb2 import CheckAccessRequest, CheckAccessResponse
from olympiad_contracts.access_pb2_grpc import add_AccessServiceServicer_to_server


class AccessServicer:
    """Принимает токен и код операции от другого сервиса."""

    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def CheckAccess(
        self, request: CheckAccessRequest, context: grpc.aio.ServicerContext
    ) -> CheckAccessResponse:
        """Читает актуальную роль и возвращает решение."""
        try:
            async with timeout(3), AsyncSession(self.engine) as db:
                account_id = await check_access(db, request.session_token, request.operation)
        except (SQLAlchemyError, OSError, TimeoutError):
            await context.abort(grpc.StatusCode.UNAVAILABLE, "Сервис доступа недоступен.")
            raise
        if account_id is None:
            return CheckAccessResponse(allowed=False)
        return CheckAccessResponse(allowed=True, account_id=str(account_id))


@asynccontextmanager
async def serve_access(engine: AsyncEngine, address: str) -> AsyncIterator[int]:
    """Поднимает сервер на заданном адресе и освобождает порт при остановке."""
    server = grpc.aio.server()
    add_AccessServiceServicer_to_server(AccessServicer(engine), server)  # type: ignore[no-untyped-call]
    port = server.add_insecure_port(address)
    await server.start()
    try:
        yield port
    finally:
        await server.stop(grace=3)
