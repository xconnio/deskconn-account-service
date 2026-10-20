"""remove apps

Revision ID: 8b1e4d2c9a70
Revises: 3f6c2a9d7b14
Create Date: 2026-10-20 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b1e4d2c9a70"
down_revision: Union[str, Sequence[str], None] = "3f6c2a9d7b14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("app_versions", schema="deskconn")
    op.drop_table("apps", schema="deskconn")


def downgrade() -> None:
    op.create_table(
        "apps",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        schema="deskconn",
    )
    op.create_table(
        "app_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("checksum", sa.Text(), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("app_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["app_id"], ["deskconn.apps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("app_id", "version", name="uq_app_versions_app_version"),
        schema="deskconn",
    )
    op.create_index(
        op.f("ix_deskconn_app_versions_app_id"), "app_versions", ["app_id"], unique=False, schema="deskconn"
    )
