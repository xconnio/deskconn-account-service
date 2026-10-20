"""remove organizations

Revision ID: 3f6c2a9d7b14
Revises: 577bf626bcf8
Create Date: 2026-10-19 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "3f6c2a9d7b14"
down_revision: Union[str, Sequence[str], None] = "577bf626bcf8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


desktop_access_role = postgresql.ENUM(
    "owner", "admin", "member", name="desktop_access_role", schema="deskconn", create_type=False
)
invitation_status = postgresql.ENUM(
    "pending", "accepted", "rejected", "expired", name="invitation_status", schema="deskconn", create_type=False
)


def upgrade() -> None:
    # desktop invites become user-only
    op.execute("DELETE FROM deskconn.desktop_invites WHERE invitee_user_id IS NULL")
    op.drop_index(
        op.f("ix_deskconn_desktop_invites_invitee_organization_id"), table_name="desktop_invites", schema="deskconn"
    )
    op.drop_column("desktop_invites", "invitee_organization_id", schema="deskconn")
    op.alter_column("desktop_invites", "invitee_user_id", nullable=False, schema="deskconn")

    op.drop_table("desktop_organization_access", schema="deskconn")
    op.drop_table("organization_invites", schema="deskconn")
    op.drop_table("organization_members", schema="deskconn")
    op.drop_table("organizations", schema="deskconn")

    sa.Enum(name="organization_invite_role", schema="deskconn").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="organization_member_role", schema="deskconn").drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["deskconn.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="deskconn",
    )
    op.create_index(
        op.f("ix_deskconn_organizations_owner_id"), "organizations", ["owner_id"], unique=False, schema="deskconn"
    )
    op.create_table(
        "organization_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("owner", "admin", "member", name="organization_member_role", schema="deskconn"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["deskconn.organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["deskconn.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="deskconn",
    )
    op.create_index(
        op.f("ix_deskconn_organization_members_organization_id"),
        "organization_members",
        ["organization_id"],
        unique=False,
        schema="deskconn",
    )
    op.create_index(
        op.f("ix_deskconn_organization_members_user_id"),
        "organization_members",
        ["user_id"],
        unique=False,
        schema="deskconn",
    )
    op.create_table(
        "organization_invites",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("owner", "admin", "member", name="organization_invite_role", schema="deskconn"),
            nullable=False,
        ),
        sa.Column("status", invitation_status, nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("inviter_id", sa.UUID(), nullable=True),
        sa.Column("invitee_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["invitee_id"], ["deskconn.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["inviter_id"], ["deskconn.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["deskconn.organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="deskconn",
    )
    op.create_index(
        op.f("ix_deskconn_organization_invites_invitee_id"),
        "organization_invites",
        ["invitee_id"],
        unique=False,
        schema="deskconn",
    )
    op.create_index(
        op.f("ix_deskconn_organization_invites_inviter_id"),
        "organization_invites",
        ["inviter_id"],
        unique=False,
        schema="deskconn",
    )
    op.create_index(
        op.f("ix_deskconn_organization_invites_organization_id"),
        "organization_invites",
        ["organization_id"],
        unique=False,
        schema="deskconn",
    )
    op.create_table(
        "desktop_organization_access",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("role", desktop_access_role, nullable=False),
        sa.Column("desktop_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["desktop_id"], ["deskconn.desktops.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["deskconn.organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("desktop_id", "organization_id", name="uq_desktop_organization_access"),
        schema="deskconn",
    )
    op.create_index(
        op.f("ix_deskconn_desktop_organization_access_desktop_id"),
        "desktop_organization_access",
        ["desktop_id"],
        unique=False,
        schema="deskconn",
    )
    op.create_index(
        op.f("ix_deskconn_desktop_organization_access_organization_id"),
        "desktop_organization_access",
        ["organization_id"],
        unique=False,
        schema="deskconn",
    )

    op.alter_column("desktop_invites", "invitee_user_id", nullable=True, schema="deskconn")
    op.add_column("desktop_invites", sa.Column("invitee_organization_id", sa.UUID(), nullable=True), schema="deskconn")
    op.create_foreign_key(
        op.f("desktop_invites_invitee_organization_id_fkey"),
        "desktop_invites",
        "organizations",
        ["invitee_organization_id"],
        ["id"],
        source_schema="deskconn",
        referent_schema="deskconn",
        ondelete="CASCADE",
    )
    op.create_index(
        op.f("ix_deskconn_desktop_invites_invitee_organization_id"),
        "desktop_invites",
        ["invitee_organization_id"],
        unique=False,
        schema="deskconn",
    )
