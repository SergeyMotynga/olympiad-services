from sqlalchemy import Engine, text


def test_migration_installs_roles(test_database: Engine) -> None:
    with test_database.connect() as db:
        roles = set(db.execute(text("SELECT code FROM roles")).scalars())

    assert roles == {"admin", "author", "representative", "reviewer"}
