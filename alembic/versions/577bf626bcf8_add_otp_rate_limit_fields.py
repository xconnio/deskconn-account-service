"""add otp rate limit fields

Revision ID: 577bf626bcf8
Revises: 1198cb3e4871
Create Date: 2026-08-25 16:35:11.915830

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "577bf626bcf8"
down_revision: Union[str, Sequence[str], None] = "1198cb3e4871"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("otp_last_sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        schema="deskconn",
    )
    op.add_column(
        "users",
        sa.Column("otp_send_count", sa.Integer(), server_default="0", nullable=True),
        schema="deskconn",
    )
    op.add_column(
        "users",
        sa.Column("otp_window_started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        schema="deskconn",
    )
    op.add_column(
        "users",
        sa.Column("otp_verify_attempts", sa.Integer(), server_default="0", nullable=True),
        schema="deskconn",
    )


def downgrade() -> None:
    op.drop_column("users", "otp_verify_attempts", schema="deskconn")
    op.drop_column("users", "otp_window_started_at", schema="deskconn")
    op.drop_column("users", "otp_send_count", schema="deskconn")
    op.drop_column("users", "otp_last_sent_at", schema="deskconn")
