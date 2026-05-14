import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Text, DateTime, Boolean, UUID, UniqueConstraint, MetaData
from sqlalchemy.orm import relationship, declarative_base, mapped_column

from deskconn import helpers


DESKCONN_SCHEMA = "deskconn"

metadata = MetaData(schema=DESKCONN_SCHEMA)
Base = declarative_base(metadata=metadata)


class OrganizationMemberRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class DesktopAccessRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class OrganizationInviteRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class InvitationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"


class CPUArchitecture(str, enum.Enum):
    amd64 = "amd64"
    arm64 = "arm64"


class OS(str, enum.Enum):
    linux = "linux"


class User(Base):
    __tablename__ = "users"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = mapped_column(Text, unique=True, nullable=False)
    password = mapped_column(Text, nullable=False)
    name = mapped_column(Text, nullable=False)
    salt = mapped_column(Text)
    otp_hash = mapped_column(Text)
    otp_expires_at = mapped_column(DateTime(timezone=True))
    is_verified = mapped_column(Boolean, default=False)

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    desktops = relationship("Desktop", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    principals = relationship("Principal", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

    organization_memberships = relationship(
        "OrganizationMember",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    organizations = relationship(
        "Organization",
        back_populates="owner",
        foreign_keys="Organization.owner_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    organization_invites_sent = relationship(
        "OrganizationInvite",
        back_populates="inviter",
        passive_deletes=True,
        foreign_keys="OrganizationInvite.inviter_id",
    )
    organization_invites_received = relationship(
        "OrganizationInvite",
        back_populates="invitee",
        passive_deletes=True,
        foreign_keys="OrganizationInvite.invitee_id",
    )

    desktop_user_accesses = relationship(
        "DesktopUserAccess", back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )

    desktop_invites_sent = relationship(
        "DesktopInvite",
        back_populates="inviter",
        passive_deletes=True,
        foreign_keys="DesktopInvite.inviter_id",
    )
    desktop_invites_received = relationship(
        "DesktopInvite",
        back_populates="invitee_user",
        passive_deletes=True,
        foreign_keys="DesktopInvite.invitee_user_id",
    )


class Principal(Base):
    __tablename__ = "principals"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_key = mapped_column(Text, nullable=False, index=True)

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)
    expires_at = mapped_column(DateTime(timezone=True), nullable=False)

    user_id = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("User", back_populates="principals", passive_deletes=True)


class Device(Base):
    __tablename__ = "devices"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = mapped_column(Text, unique=True, nullable=False)
    name = mapped_column(Text)
    public_key = mapped_column(Text, nullable=False, index=True)

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    user_id = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("User", back_populates="devices", passive_deletes=True)


class Desktop(Base):
    __tablename__ = "desktops"

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_desktop_user_name"),)

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    authid = mapped_column(Text, unique=True, nullable=False)
    name = mapped_column(Text, nullable=False)
    public_key = mapped_column(Text, nullable=False, index=True)
    realm = mapped_column(Text, nullable=False, unique=True)

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    user_id = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("User", back_populates="desktops", passive_deletes=True)

    user_accesses = relationship(
        "DesktopUserAccess", back_populates="desktop", cascade="all, delete-orphan", passive_deletes=True
    )
    organization_accesses = relationship(
        "DesktopOrganizationAccess", back_populates="desktop", cascade="all, delete-orphan", passive_deletes=True
    )
    invites = relationship(
        "DesktopInvite", back_populates="desktop", cascade="all, delete-orphan", passive_deletes=True
    )


class Organization(Base):
    __tablename__ = "organizations"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(Text, nullable=False)

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    owner_id = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    owner = relationship(
        "User", back_populates="organizations", cascade="all, delete-orphan", passive_deletes=True, single_parent=True
    )

    members = relationship(
        "OrganizationMember", back_populates="organization", cascade="all, delete-orphan", passive_deletes=True
    )

    invites = relationship(
        "OrganizationInvite", back_populates="organization", cascade="all, delete-orphan", passive_deletes=True
    )

    desktop_accesses = relationship(
        "DesktopOrganizationAccess", back_populates="organization", cascade="all, delete-orphan", passive_deletes=True
    )

    desktop_invites = relationship(
        "DesktopInvite",
        back_populates="invitee_organization",
        passive_deletes=True,
        foreign_keys="DesktopInvite.invitee_organization_id",
    )


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = mapped_column(
        Enum(OrganizationMemberRole, name="organization_member_role", schema=DESKCONN_SCHEMA), nullable=False
    )

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    organization_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization = relationship("Organization", back_populates="members")

    user_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user = relationship("User", back_populates="organization_memberships")


class DesktopUserAccess(Base):
    __tablename__ = "desktop_user_access"

    __table_args__ = (UniqueConstraint("desktop_id", "user_id", name="uq_desktop_user_access"),)

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = mapped_column(Enum(DesktopAccessRole, name="desktop_access_role", schema=DESKCONN_SCHEMA), nullable=False)

    desktop_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("desktops.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    desktop = relationship("Desktop", back_populates="user_accesses")
    user = relationship("User", back_populates="desktop_user_accesses")


class DesktopOrganizationAccess(Base):
    __tablename__ = "desktop_organization_access"

    __table_args__ = (UniqueConstraint("desktop_id", "organization_id", name="uq_desktop_organization_access"),)

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = mapped_column(Enum(DesktopAccessRole, name="desktop_access_role", schema=DESKCONN_SCHEMA), nullable=False)

    desktop_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("desktops.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    desktop = relationship("Desktop", back_populates="organization_accesses")
    organization = relationship("Organization", back_populates="desktop_accesses")


class DesktopInvite(Base):
    __tablename__ = "desktop_invites"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = mapped_column(Enum(DesktopAccessRole, name="desktop_access_role", schema=DESKCONN_SCHEMA), nullable=False)
    status = mapped_column(
        Enum(InvitationStatus, name="invitation_status", schema=DESKCONN_SCHEMA),
        nullable=False,
        default=InvitationStatus.pending.value,
    )

    accepted_at = mapped_column(DateTime(timezone=True))
    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)
    expires_at = mapped_column(DateTime(timezone=True), nullable=False)

    desktop_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("desktops.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inviter_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Exactly one of these is set depending on whether the invite is for a user or an organization
    invitee_user_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    invitee_organization_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )

    desktop = relationship("Desktop", back_populates="invites")
    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="desktop_invites_sent")
    invitee_user = relationship("User", foreign_keys=[invitee_user_id], back_populates="desktop_invites_received")
    invitee_organization = relationship(
        "Organization", foreign_keys=[invitee_organization_id], back_populates="desktop_invites"
    )


class OrganizationInvite(Base):
    __tablename__ = "organization_invites"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = mapped_column(
        Enum(OrganizationInviteRole, name="organization_invite_role", schema=DESKCONN_SCHEMA), nullable=False
    )
    status = mapped_column(
        Enum(InvitationStatus, name="invitation_status", schema=DESKCONN_SCHEMA),
        nullable=False,
        default=InvitationStatus.pending.value,
    )

    accepted_at = mapped_column(DateTime(timezone=True))
    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)
    expires_at = mapped_column(DateTime(timezone=True), nullable=False)

    organization_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization = relationship("Organization", back_populates="invites")

    inviter_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="organization_invites_sent")

    invitee_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    invitee = relationship("User", foreign_keys=[invitee_id], back_populates="organization_invites_received")


class App(Base):
    __tablename__ = "apps"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(Text, unique=True, nullable=False)
    last_updated = mapped_column(DateTime(timezone=True))

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    versions = relationship(
        "AppVersion",
        back_populates="app",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AppVersion(Base):
    __tablename__ = "app_versions"

    __table_args__ = (UniqueConstraint("app_id", "version", name="uq_app_versions_app_version"),)

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = mapped_column(Text, nullable=False)
    checksum = mapped_column(Text)
    released_at = mapped_column(DateTime(timezone=True), nullable=False, default=helpers.utcnow)

    app_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("apps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    app = relationship("App", back_populates="versions", passive_deletes=True)
