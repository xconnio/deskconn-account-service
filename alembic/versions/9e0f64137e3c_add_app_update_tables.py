"""add app update tables

Revision ID: 9e0f64137e3c
Revises: f5c9cb9d3e6f
Create Date: 2026-04-02 18:50:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9e0f64137e3c"
down_revision: Union[str, Sequence[str], None] = "f5c9cb9d3e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "apps",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "app_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("checksum", sa.Text(), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("app_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["app_id"], ["apps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("app_id", "version", name="uq_app_versions_app_version"),
    )
    op.create_index(op.f("ix_app_versions_app_id"), "app_versions", ["app_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_app_versions_app_id"), table_name="app_versions")
    op.drop_table("app_versions")
    op.drop_table("apps")
