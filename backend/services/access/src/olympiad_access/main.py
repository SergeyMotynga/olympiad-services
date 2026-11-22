"""Точка входа сервиса «Доступ и роли»."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from os import getenv

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from olympiad_access.api import router
from olympiad_access.grpc_server import serve_access
from olympiad_runtime.app import create_app, lifespan


@asynccontextmanager
async def access_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Запускает HTTP и внутренний gRPC с общим пулом PostgreSQL."""
    async with lifespan(app):
        address = getenv("ACCESS_GRPC_ADDRESS")
        if address:
            engine: AsyncEngine = app.state.database
            async with serve_access(engine, address):
                yield
        else:
            yield


app = create_app("Доступ и роли", app_lifespan=access_lifespan)
app.include_router(router)
