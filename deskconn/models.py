import enum
import uuid

from sqlalchemy import Enum, Integer, ForeignKey, Text, DateTime, Boolean, UUID
from sqlalchemy.orm import relationship, declarative_base, mapped_column

from deskconn import helpers

Base = declarative_base()


class UserRole(str, enum.Enum):
    guest = "guest"
    user = "user"


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
