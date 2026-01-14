import enum
import uuid

from sqlalchemy import Enum, Integer, ForeignKey, Text, DateTime, Boolean, UUID
from sqlalchemy.orm import relationship, declarative_base, mapped_column

from deskconn import helpers

Base = declarative_base()


class UserRole(str, enum.Enum):
    guest = "guest"
    user = "user"


class OrganizationRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class InvitationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"


class User(Base):
    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True)
    email = mapped_column(Text, unique=True, nullable=False)
    password = mapped_column(Text, nullable=False)
    name = mapped_column(Text, nullable=False)
    salt = mapped_column(Text)
    role = mapped_column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.guest)
    otp_hash = mapped_column(Text)
    otp_expires_at = mapped_column(DateTime(timezone=True))
    is_verified = mapped_column(Boolean, default=False)

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    desktops = relationship("Desktop", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

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

    inviter = relationship(
        "OrganizationInvite",
        back_populates="inviter",
        passive_deletes=True,
        foreign_keys="OrganizationInvite.inviter_id",
    )
    invitee = relationship(
        "OrganizationInvite",
        back_populates="invitee",
        passive_deletes=True,
        foreign_keys="OrganizationInvite.invitee_id",
    )


class Device(Base):
    __tablename__ = "devices"

    id = mapped_column(Integer, primary_key=True)
    device_id = mapped_column(Text, unique=True, nullable=False)
    name = mapped_column(Text)
    public_key = mapped_column(Text, nullable=False, index=True)

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    user = relationship("User", back_populates="devices", passive_deletes=True)


class Desktop(Base):
    __tablename__ = "desktops"

    id = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    authid = mapped_column(Text, unique=True, nullable=False)
    name = mapped_column(Text)
    public_key = mapped_column(Text, nullable=False, index=True)

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("User", back_populates="desktops", passive_deletes=True)
    organization_id = mapped_column(
        UUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    realm = mapped_column(Text, nullable=False)

    organization = relationship("Organization", back_populates="desktops")
    accesses = relationship(
        "DesktopAccess", back_populates="desktop", cascade="all, delete-orphan", passive_deletes=True
    )


class Organization(Base):
    __tablename__ = "organizations"

    id = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    name = mapped_column(Text, nullable=False)

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    owner_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    owner = relationship(
        "User", back_populates="organizations", cascade="all, delete-orphan", passive_deletes=True, single_parent=True
    )

    members = relationship(
        "OrganizationMember", back_populates="organization", cascade="all, delete-orphan", passive_deletes=True
    )

    desktops = relationship(
        "Desktop", back_populates="organization", cascade="all, delete-orphan", passive_deletes=True
    )

    invites = relationship(
        "OrganizationInvite", back_populates="organization", cascade="all, delete-orphan", passive_deletes=True
    )


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    role = mapped_column(Enum(OrganizationRole, name="organization_role"), nullable=False)

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    organization_id = mapped_column(
        UUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization = relationship("Organization", back_populates="members")

    user_id = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user = relationship("User", back_populates="organization_memberships")

    desktop_access = relationship(
        "DesktopAccess",
        back_populates="member",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DesktopAccess(Base):
    __tablename__ = "desktop_access"

    id = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    role = mapped_column(Enum(OrganizationRole, name="organization_role"), nullable=False)

    member_id = mapped_column(
        UUID, ForeignKey("organization_members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    desktop_id = mapped_column(UUID, ForeignKey("desktops.id", ondelete="CASCADE"), nullable=False, index=True)

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    member = relationship("OrganizationMember", back_populates="desktop_access")
    desktop = relationship("Desktop", back_populates="accesses")


class OrganizationInvite(Base):
    __tablename__ = "organization_invites"

    id = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    role = mapped_column(Enum(OrganizationRole, name="organization_role"), nullable=False)
    status = mapped_column(
        Enum(InvitationStatus, name="invitation_status"), nullable=False, default=InvitationStatus.pending.value
    )

    accepted_at = mapped_column(DateTime(timezone=True))
    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)
    expires_at = mapped_column(DateTime(timezone=True), nullable=False)

    organization_id = mapped_column(
        UUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization = relationship("Organization", back_populates="invites")

    # Filled once invite is accepted or user exists in database
    inviter_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="inviter")

    invitee_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    invitee = relationship("User", foreign_keys=[invitee_id], back_populates="invitee")
