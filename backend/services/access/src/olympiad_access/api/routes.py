"""Обработка ошибок входных данных на защищённых маршрутах."""

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from olympiad_access.api.deps import bearer, get_auth_service, require_token
from olympiad_access.api.errors import account_error
from olympiad_access.exceptions.access import AccessError


class ProtectedWriteRoute(APIRoute):
    """Проверяет право с кодом в имени маршрута перед ответом об ошибке валидации."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handle = super().get_route_handler()

        async def handle_request(request: Request) -> Response:
            try:
                return await handle(request)
            except RequestValidationError:
                # При ошибке FastAPI не вызывает сценарий, где обычно проверяются права.
                token = require_token(await bearer(request))
                engine: AsyncEngine = request.app.state.database
                try:
                    async with AsyncSession(engine) as db, db.begin():
                        await get_auth_service(db).require_operation(token, self.name)
                except AccessError as error:
                    raise account_error(error) from error
                raise

        return handle_request
