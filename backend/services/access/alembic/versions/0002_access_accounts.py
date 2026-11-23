"""Создаёт справочник ролей, аккаунты и сессии."""

import sqlalchemy as sa
from alembic import op

revision = "access_0002"
down_revision = "access_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    roles = op.create_table(
        "roles",
        sa.Column("id", sa.SmallInteger(), sa.Identity(), primary_key=True),
        sa.Column("code", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
    )
    op.bulk_insert(
        roles,
        [
            {"code": "admin", "name": "Администратор"},
            {"code": "author", "name": "Составитель заданий"},
            {"code": "representative", "name": "Представитель"},
            {"code": "reviewer", "name": "Проверяющий"},
        ],
    )
    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("login", sa.String(32), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role_id", sa.SmallInteger(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("login", name="uq_accounts_login"),
        sa.CheckConstraint(
            "login ~ '^[a-z0-9][a-z0-9._-]{2,31}$'", name="ck_accounts_login_format"
        ),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("expires_at > created_at", name="ck_sessions_expiration"),
        sa.CheckConstraint("octet_length(token_hash) = 32", name="ck_sessions_token_hash_length"),
    )
    op.create_index("ix_sessions_account_id", "sessions", ["account_id"])


def downgrade() -> None:
    op.drop_table("sessions")
    op.drop_table("accounts")
    op.drop_table("roles")
