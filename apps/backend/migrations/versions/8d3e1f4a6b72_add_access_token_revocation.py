"""Add access-token revocation state.

Revision ID: 8d3e1f4a6b72
Revises: ff73bbcb94d4
Create Date: 2026-09-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "8d3e1f4a6b72"
down_revision = "ff73bbcb94d4"
branch_labels = None
depends_on = None


def upgrade():
    """Add per-user invalidation time and explicit JWT revocation storage."""

    op.add_column(
        "users",
        sa.Column("tokens_valid_after", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "token_blocklist",
        sa.Column("jti", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_type", sa.String(length=20), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_token_blocklist_jti", "token_blocklist", ["jti"], unique=True
    )
    op.create_index(
        "ix_token_blocklist_user_id", "token_blocklist", ["user_id"], unique=False
    )


def downgrade():
    """Remove explicit and per-user access-token revocation state."""

    op.drop_index("ix_token_blocklist_user_id", table_name="token_blocklist")
    op.drop_index("ix_token_blocklist_jti", table_name="token_blocklist")
    op.drop_table("token_blocklist")
    op.drop_column("users", "tokens_valid_after")
