import enum
from datetime import datetime, timezone

from sqlalchemy import Enum, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship, declarative_base, mapped_column

Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    guest = "guest"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True)
    email = mapped_column(Text, unique=True, nullable=False)
    password = mapped_column(Text, nullable=False)
    name = mapped_column(Text, nullable=False)
    role = mapped_column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.guest)

    created_at = mapped_column(DateTime(timezone=True), default=utcnow)

    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    desktops = relationship("Desktop", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)


class Device(Base):
    __tablename__ = "devices"

    id = mapped_column(Integer, primary_key=True)
    device_id = mapped_column(Text, unique=True, nullable=False)
    name = mapped_column(Text)
    public_key = mapped_column(Text, nullable=False, index=True)

    created_at = mapped_column(DateTime(timezone=True), default=utcnow)

    user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    user = relationship("User", back_populates="devices", cascade="all, delete-orphan", passive_deletes=True)
    desktops = relationship("Desktop", back_populates="device", cascade="all, delete-orphan", passive_deletes=True)


class Desktop(Base):
    __tablename__ = "desktops"

    id = mapped_column(Integer, primary_key=True)
    desktop_id = mapped_column(Text, unique=True, nullable=False)
    name = mapped_column(Text)
    public_key = mapped_column(Text, nullable=False, index=True)

    created_at = mapped_column(DateTime(timezone=True), default=utcnow)

    user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("User", back_populates="desktops", cascade="all, delete-orphan", passive_deletes=True)

    device_id = mapped_column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    device = relationship("Device", back_populates="devices", cascade="all, delete-orphan", passive_deletes=True)
