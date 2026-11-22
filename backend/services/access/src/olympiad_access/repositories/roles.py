"""Запросы к справочнику ролей."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from olympiad_access.domain.roles import RoleCode
from olympiad_access.models.accounts import Role


async def lock_role_id(db: AsyncSession, code: RoleCode) -> int:
    """Находит и блокирует роль на время создания первого администратора."""
    query = select(Role.id).where(Role.code == code).with_for_update()
    return (await db.execute(query)).scalar_one()


async def role_exists(db: AsyncSession, role_id: int) -> bool:
    """Проверяет наличие роли по идентификатору."""
    return await db.get(Role, role_id) is not None


async def list_roles(db: AsyncSession) -> Sequence[Role]:
    """Читает справочник ролей."""
    return (await db.scalars(select(Role).order_by(Role.id))).all()
