from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI

from olympiad_runtime.api import readiness_router
from olympiad_runtime.config import Settings
from olympiad_runtime.repositories.database import build_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Создаёт пул соединений и освобождает его при остановке."""
    engine = build_engine(Settings().connection_url)
    app.state.database = engine
    try:
        yield
    finally:
        await engine.dispose()


def create_app(
    title: str,
    *,
    app_lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] = lifespan,
) -> FastAPI:
    """Создаёт приложение с проверкой готовности."""
    app = FastAPI(title=title, lifespan=app_lifespan)
    app.include_router(readiness_router)
    return app
