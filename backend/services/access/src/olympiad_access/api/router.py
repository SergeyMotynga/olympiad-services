"""Объединяет HTTP-маршруты сервиса доступа."""

from fastapi import APIRouter

from olympiad_access.api.v1.accounts import router as accounts_router
from olympiad_access.api.v1.auth import page_router
from olympiad_access.api.v1.auth import router as auth_router
from olympiad_access.api.v1.roles import router as roles_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(accounts_router)
api_router.include_router(roles_router)
api_router.include_router(page_router)
