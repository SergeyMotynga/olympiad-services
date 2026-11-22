"""Точка входа сервиса «Доступ и роли»."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncEngine

from olympiad_access.api.errors import request_validation_error
from olympiad_access.api.grpc import serve_access
from olympiad_access.api.router import api_router
from olympiad_access.core.config import AccessSettings
from olympiad_runtime.app import create_app, lifespan


@asynccontextmanager
async def access_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Запускает HTTP и внутренний gRPC с общим пулом PostgreSQL."""
    async with lifespan(app):
        address = AccessSettings().access_grpc_address
        if address:
            engine: AsyncEngine = app.state.database
            async with serve_access(engine, address):
                yield
        else:
            yield


app = create_app("Доступ и роли", app_lifespan=access_lifespan)
app.exception_handler(RequestValidationError)(request_validation_error)
app.include_router(api_router)
