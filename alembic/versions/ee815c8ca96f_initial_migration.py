"""initial migration

Revision ID: ee815c8ca96f
Revises:
Create Date: 2026-04-09 14:14:05.283133

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ee815c8ca96f"
down_revision: Union[str, Sequence[str], None] = None
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
        schema="deskconn",
    )
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("salt", sa.Text(), nullable=True),
        sa.Column("otp_hash", sa.Text(), nullable=True),
        sa.Column("otp_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
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
    op.create_table(
        "devices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("device_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["deskconn.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id"),
        schema="deskconn",
    )
    op.create_index(op.f("ix_deskconn_devices_public_key"), "devices", ["public_key"], unique=False, schema="deskconn")
    op.create_index(op.f("ix_deskconn_devices_user_id"), "devices", ["user_id"], unique=False, schema="deskconn")
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
        "principals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["deskconn.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="deskconn",
    )
    op.create_index(
        op.f("ix_deskconn_principals_public_key"), "principals", ["public_key"], unique=False, schema="deskconn"
    )
    op.create_index(op.f("ix_deskconn_principals_user_id"), "principals", ["user_id"], unique=False, schema="deskconn")
    op.create_table(
        "desktops",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("authid", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("realm", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["deskconn.organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["deskconn.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("authid"),
        sa.UniqueConstraint("organization_id", "name", name="uq_desktop_org_name"),
        sa.UniqueConstraint("realm"),
        schema="deskconn",
    )
    op.create_index(
        op.f("ix_deskconn_desktops_organization_id"), "desktops", ["organization_id"], unique=False, schema="deskconn"
    )
    op.create_index(
        op.f("ix_deskconn_desktops_public_key"), "desktops", ["public_key"], unique=False, schema="deskconn"
    )
    op.create_index(op.f("ix_deskconn_desktops_user_id"), "desktops", ["user_id"], unique=False, schema="deskconn")
    op.create_table(
        "organization_invites",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("owner", "admin", "member", name="organization_invite_role", schema="deskconn"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "accepted", "rejected", "expired", name="invitation_status", schema="deskconn"),
            nullable=False,
        ),
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
        "desktop_access",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "role", sa.Enum("owner", "admin", "member", name="desktop_access_role", schema="deskconn"), nullable=False
        ),
        sa.Column("member_id", sa.UUID(), nullable=False),
        sa.Column("desktop_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["desktop_id"], ["deskconn.desktops.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["deskconn.organization_members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="deskconn",
    )
    op.create_index(
        op.f("ix_deskconn_desktop_access_desktop_id"), "desktop_access", ["desktop_id"], unique=False, schema="deskconn"
    )
    op.create_index(
        op.f("ix_deskconn_desktop_access_member_id"), "desktop_access", ["member_id"], unique=False, schema="deskconn"
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_deskconn_desktop_access_member_id"), table_name="desktop_access", schema="deskconn")
    op.drop_index(op.f("ix_deskconn_desktop_access_desktop_id"), table_name="desktop_access", schema="deskconn")
    op.drop_table("desktop_access", schema="deskconn")
    op.drop_index(
        op.f("ix_deskconn_organization_members_user_id"), table_name="organization_members", schema="deskconn"
    )
    op.drop_index(
        op.f("ix_deskconn_organization_members_organization_id"), table_name="organization_members", schema="deskconn"
    )
    op.drop_table("organization_members", schema="deskconn")
    op.drop_index(
        op.f("ix_deskconn_organization_invites_organization_id"), table_name="organization_invites", schema="deskconn"
    )
    op.drop_index(
        op.f("ix_deskconn_organization_invites_inviter_id"), table_name="organization_invites", schema="deskconn"
    )
    op.drop_index(
        op.f("ix_deskconn_organization_invites_invitee_id"), table_name="organization_invites", schema="deskconn"
    )
    op.drop_table("organization_invites", schema="deskconn")
    op.drop_index(op.f("ix_deskconn_desktops_user_id"), table_name="desktops", schema="deskconn")
    op.drop_index(op.f("ix_deskconn_desktops_public_key"), table_name="desktops", schema="deskconn")
    op.drop_index(op.f("ix_deskconn_desktops_organization_id"), table_name="desktops", schema="deskconn")
    op.drop_table("desktops", schema="deskconn")
    op.drop_index(op.f("ix_deskconn_principals_user_id"), table_name="principals", schema="deskconn")
    op.drop_index(op.f("ix_deskconn_principals_public_key"), table_name="principals", schema="deskconn")
    op.drop_table("principals", schema="deskconn")
    op.drop_index(op.f("ix_deskconn_organizations_owner_id"), table_name="organizations", schema="deskconn")
    op.drop_table("organizations", schema="deskconn")
    op.drop_index(op.f("ix_deskconn_devices_user_id"), table_name="devices", schema="deskconn")
    op.drop_index(op.f("ix_deskconn_devices_public_key"), table_name="devices", schema="deskconn")
    op.drop_table("devices", schema="deskconn")
    op.drop_index(op.f("ix_deskconn_app_versions_app_id"), table_name="app_versions", schema="deskconn")
    op.drop_table("app_versions", schema="deskconn")
    op.drop_table("users", schema="deskconn")
    op.drop_table("apps", schema="deskconn")
    sa.Enum(name="invitation_status", schema="deskconn").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="organization_invite_role", schema="deskconn").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="organization_member_role", schema="deskconn").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="desktop_access_role", schema="deskconn").drop(op.get_bind(), checkfirst=True)
