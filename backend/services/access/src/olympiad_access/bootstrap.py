"""Команда создания первого администратора."""

import argparse
import sys
from asyncio import run
from getpass import getpass

from sqlalchemy.ext.asyncio import AsyncSession

from olympiad_access.exceptions.access import AccessError
from olympiad_access.services.accounts import AccountService
from olympiad_runtime.config import Settings
from olympiad_runtime.repositories.database import build_engine


async def create_first_admin(login: str, password: str) -> None:
    """Открывает соединение с базой на время создания аккаунта."""
    engine = build_engine(Settings().connection_url)
    try:
        async with AsyncSession(engine) as db:
            await AccountService(db).bootstrap_admin(login, password)
    finally:
        await engine.dispose()


def main() -> None:
    """Читает логин и пароль и создаёт первый аккаунт."""
    parser = argparse.ArgumentParser(description="Создать первого администратора.")
    parser.add_argument("--login", required=True, help="Логин администратора.")
    parser.add_argument("--password-stdin", action="store_true", help="Прочитать пароль из stdin.")
    args = parser.parse_args()
    if args.password_stdin:
        password = sys.stdin.readline().removesuffix("\r\n").removesuffix("\n")
    else:
        password = getpass("Пароль: ")
    try:
        run(create_first_admin(args.login, password))
    except AccessError as error:
        parser.exit(1, f"{error}\n")
    print("Аккаунт администратора создан.")


if __name__ == "__main__":
    main()
