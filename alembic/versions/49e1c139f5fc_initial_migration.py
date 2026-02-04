"""initial migration

Revision ID: 49e1c139f5fc
Revises:
Create Date: 2026-02-04 14:14:43.690864

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "49e1c139f5fc"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    )
    op.create_table(
        "devices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("device_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id"),
    )
    op.create_index(op.f("ix_devices_public_key"), "devices", ["public_key"], unique=False)
    op.create_index(op.f("ix_devices_user_id"), "devices", ["user_id"], unique=False)
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_organizations_owner_id"), "organizations", ["owner_id"], unique=False)
    op.create_table(
        "principals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_principals_public_key"), "principals", ["public_key"], unique=False)
    op.create_index(op.f("ix_principals_user_id"), "principals", ["user_id"], unique=False)
    op.create_table(
        "desktops",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("authid", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("realm", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("authid"),
        sa.UniqueConstraint("realm"),
    )
    op.create_index(op.f("ix_desktops_organization_id"), "desktops", ["organization_id"], unique=False)
    op.create_index(op.f("ix_desktops_public_key"), "desktops", ["public_key"], unique=False)
    op.create_index(op.f("ix_desktops_user_id"), "desktops", ["user_id"], unique=False)
    op.create_table(
        "organization_invites",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("role", sa.Enum("owner", "admin", "member", name="organization_role"), nullable=False),
        sa.Column(
            "status", sa.Enum("pending", "accepted", "rejected", "expired", name="invitation_status"), nullable=False
        ),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("inviter_id", sa.UUID(), nullable=True),
        sa.Column("invitee_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["invitee_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["inviter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_organization_invites_invitee_id"), "organization_invites", ["invitee_id"], unique=False)
    op.create_index(op.f("ix_organization_invites_inviter_id"), "organization_invites", ["inviter_id"], unique=False)
    op.create_index(
        op.f("ix_organization_invites_organization_id"), "organization_invites", ["organization_id"], unique=False
    )
    op.create_table(
        "organization_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("role", sa.Enum("owner", "admin", "member", name="organization_role"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_organization_members_organization_id"), "organization_members", ["organization_id"], unique=False
    )
    op.create_index(op.f("ix_organization_members_user_id"), "organization_members", ["user_id"], unique=False)
    op.create_table(
        "desktop_access",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("role", sa.Enum("owner", "admin", "member", name="organization_role"), nullable=False),
        sa.Column("member_id", sa.UUID(), nullable=False),
        sa.Column("desktop_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["desktop_id"], ["desktops.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["organization_members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_desktop_access_desktop_id"), "desktop_access", ["desktop_id"], unique=False)
    op.create_index(op.f("ix_desktop_access_member_id"), "desktop_access", ["member_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_desktop_access_member_id"), table_name="desktop_access")
    op.drop_index(op.f("ix_desktop_access_desktop_id"), table_name="desktop_access")
    op.drop_table("desktop_access")
    op.drop_index(op.f("ix_organization_members_user_id"), table_name="organization_members")
    op.drop_index(op.f("ix_organization_members_organization_id"), table_name="organization_members")
    op.drop_table("organization_members")
    op.drop_index(op.f("ix_organization_invites_organization_id"), table_name="organization_invites")
    op.drop_index(op.f("ix_organization_invites_inviter_id"), table_name="organization_invites")
    op.drop_index(op.f("ix_organization_invites_invitee_id"), table_name="organization_invites")
    op.drop_table("organization_invites")
    op.drop_index(op.f("ix_desktops_user_id"), table_name="desktops")
    op.drop_index(op.f("ix_desktops_public_key"), table_name="desktops")
    op.drop_index(op.f("ix_desktops_organization_id"), table_name="desktops")
    op.drop_table("desktops")
    op.drop_index(op.f("ix_principals_user_id"), table_name="principals")
    op.drop_index(op.f("ix_principals_public_key"), table_name="principals")
    op.drop_table("principals")
    op.drop_index(op.f("ix_organizations_owner_id"), table_name="organizations")
    op.drop_table("organizations")
    op.drop_index(op.f("ix_devices_user_id"), table_name="devices")
    op.drop_index(op.f("ix_devices_public_key"), table_name="devices")
    op.drop_table("devices")
    op.drop_table("users")
