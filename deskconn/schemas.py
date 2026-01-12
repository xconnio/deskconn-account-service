from __future__ import annotations

from datetime import datetime
from uuid import UUID
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, UUID4, PlainSerializer, StringConstraints, Field, EmailStr

from deskconn import helpers, models
from deskconn.models import UserRole

# serialize UUID as string for JSON responses
UUIDStr = Annotated[UUID4, PlainSerializer(lambda v: str(v), return_type=str)]

DateTimeStr = Annotated[datetime, PlainSerializer(lambda v: v.isoformat(), return_type=str)]
PublicKeyHex = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
    ),
]


class User(BaseModel):
    email: str
    name: str
    role: UserRole


class UserCreate(User):
    password: str


class UserUpgrade(BaseModel):
    old_email: str
    email: str
    password: str
    name: str | None = None


class UserVerify(BaseModel):
    email: str
    code: str


class UserGet(User):
    model_config = ConfigDict(from_attributes=True)

    id: int


class UserUpdate(BaseModel):
    name: str | None = None
    password: str | None = None


class PasswordReset(BaseModel):
    email: str
    password: str
    code: str


class CRAUser(UserGet):
    model_config = ConfigDict(from_attributes=True)

    salt: str
    password: str
    authrole: str = helpers.ROLE_USER
    iterations: int = helpers.ITERATIONS
    key_length: int = helpers.KEY_LENGTH


class DeviceCreate(BaseModel):
    device_id: str
    public_key: PublicKeyHex
    name: str | None = None


class DeviceGet(DeviceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class DesktopCreate(BaseModel):
    authid: str
    public_key: PublicKeyHex
    organization_id: UUID4
    name: str | None = None


class DesktopGet(DesktopCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUIDStr
    organization_id: UUIDStr


class DesktopDelete(BaseModel):
    id: UUID4


class DesktopUpdate(DesktopDelete):
    public_key: PublicKeyHex | None = None
    name: str | None = None


class DesktopAccessGrant(BaseModel):
    id: UUID4
    invitee: EmailStr
    role: AllowedInviteRoles


class DesktopAccessGet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUIDStr
    desktop_id: UUIDStr
    created_at: DateTimeStr


class OrganizationMemberGet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    role: models.OrganizationRole
    user: UserGet


class OrganizationMemberList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUIDStr
    name: str

    owner: UserGet
    members: list[OrganizationMemberGet] = []


class OrganizationCreate(BaseModel):
    name: str


class OrganizationGet(OrganizationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUIDStr


class OrganizationDelete(BaseModel):
    organization_id: UUID


class OrganizationUpdate(OrganizationDelete):
    organization_id: UUID
    name: str | None = None


AllowedInviteRoles = Literal[
    models.OrganizationRole.admin,
    models.OrganizationRole.member,
]


class OrganizationInviteCreate(BaseModel):
    organization_id: UUID
    email: EmailStr
    role: AllowedInviteRoles
    expires_in_hours: int = Field(default=72, ge=1, le=168)


class OrganizationInviteGet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUIDStr
    organization_id: UUIDStr
    role: models.OrganizationRole
    status: models.InvitationStatus
    expires_at: DateTimeStr
    created_at: DateTimeStr


OrganizationRespondStatus = Literal[
    models.InvitationStatus.accepted,
    models.InvitationStatus.rejected,
]


class OrganizationInviteRespond(BaseModel):
    invitation_id: UUID4
    status: OrganizationRespondStatus
