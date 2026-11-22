"""HTTP-проверка готовности приложения."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncEngine

from olympiad_runtime.services.readiness import is_database_ready

readiness_router = APIRouter()


@readiness_router.get("/ready", responses={503: {"description": "База данных недоступна"}})
async def readiness(request: Request) -> JSONResponse:
    """Проверяет, что приложение может выполнить запрос к своей базе."""
    database: AsyncEngine = request.app.state.database
    if not await is_database_ready(database):
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return JSONResponse({"status": "ready"})
