import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Text, DateTime, Boolean, Integer, UUID, UniqueConstraint, MetaData, func
from sqlalchemy.orm import relationship, declarative_base, mapped_column

from deskconn import helpers


DESKCONN_SCHEMA = "deskconn"

metadata = MetaData(schema=DESKCONN_SCHEMA)
Base = declarative_base(metadata=metadata)


class DesktopAccessRole(str, enum.Enum):
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

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = mapped_column(Text, unique=True, nullable=False)
    password = mapped_column(Text, nullable=False)
    name = mapped_column(Text, nullable=False)
    salt = mapped_column(Text)
    otp_hash = mapped_column(Text)
    otp_expires_at = mapped_column(DateTime(timezone=True))
    otp_purpose = mapped_column(Text, server_default=None)
    otp_last_sent_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    otp_send_count = mapped_column(Integer, server_default="0")
    otp_window_started_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    otp_verify_attempts = mapped_column(Integer, server_default="0")
    is_verified = mapped_column(Boolean, default=False)

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    desktops = relationship("Desktop", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    principals = relationship("Principal", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

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
    invites = relationship(
        "DesktopInvite", back_populates="desktop", cascade="all, delete-orphan", passive_deletes=True
    )


class DesktopUserAccess(Base):
    __tablename__ = "desktop_user_access"

    __table_args__ = (UniqueConstraint("desktop_id", "user_id", name="uq_desktop_user_access"),)

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = mapped_column(Enum(DesktopAccessRole, name="desktop_access_role", schema=DESKCONN_SCHEMA), nullable=False)

    desktop_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("desktops.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    created_at = mapped_column(DateTime(timezone=True), default=helpers.utcnow)

    desktop = relationship("Desktop", back_populates="user_accesses")
    user = relationship("User", back_populates="desktop_user_accesses")


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
    invitee_user_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    desktop = relationship("Desktop", back_populates="invites")
    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="desktop_invites_sent")
    invitee_user = relationship("User", foreign_keys=[invitee_user_id], back_populates="desktop_invites_received")
