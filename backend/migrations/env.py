from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url

from olympiad_runtime.config import Settings


def run_migrations() -> None:
    """Применяет ревизии к базе выбранного сервиса."""
    database_url = context.config.attributes.get("database_url") or Settings().connection_url
    url = make_url(database_url).set(drivername="postgresql+psycopg")
    if context.is_offline_mode():
        context.configure(url=url, literal_binds=True, dialect_opts={"paramstyle": "named"})
        with context.begin_transaction():
            context.run_migrations()
        return

    engine = create_engine(url, poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run_migrations()
