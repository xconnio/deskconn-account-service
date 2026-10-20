from __future__ import annotations

from typing import Annotated, Literal
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from pydantic import BaseModel, ConfigDict, UUID4, PlainSerializer, StringConstraints, Field, EmailStr

from deskconn import helpers, models

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
    public_key: PublicKeyHex


class UserGet(User):
    model_config = ConfigDict(from_attributes=True)

    id: UUIDStr


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
    authrole: str = helpers.ROLE_CRA_USER
    iterations: int = helpers.ITERATIONS
    key_length: int = helpers.KEY_LENGTH


class DeviceCreate(BaseModel):
    device_id: str
    public_key: PublicKeyHex
    name: str | None = None


class DeviceGet(DeviceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUIDStr


class DesktopCreate(BaseModel):
    authid: str
    public_key: PublicKeyHex
    name: str


class DesktopList(BaseModel):
    name: str | None = None


class DesktopGet(DesktopCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUIDStr
    realm: str
    user_id: UUIDStr


class DesktopDetach(BaseModel):
    authid: str


class DesktopUpdate(BaseModel):
    id: UUID4
    public_key: PublicKeyHex | None = None
    name: str | None = None


class DesktopUserInviteCreate(BaseModel):
    desktop_id: UUID4
    email: EmailStr
    role: Literal[models.DesktopAccessRole.admin, models.DesktopAccessRole.member]
    expires_in_hours: int = Field(default=72, ge=1, le=168)


class DesktopInviteGet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUIDStr
    desktop_id: UUIDStr
    role: models.DesktopAccessRole
    status: models.InvitationStatus
    expires_at: DateTimeStr
    created_at: DateTimeStr
    invitee_user_id: UUIDStr


DesktopInviteRespondStatus = Literal[
    models.InvitationStatus.accepted,
    models.InvitationStatus.rejected,
]


class DesktopInviteRespond(BaseModel):
    invitation_id: UUID4
    status: DesktopInviteRespondStatus


class DesktopUserAccessGet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUIDStr
    desktop_id: UUIDStr
    user_id: UUIDStr
    role: models.DesktopAccessRole
    created_at: DateTimeStr


class DesktopAccessRoleUpdate(BaseModel):
    access_id: UUID4
    role: Literal[models.DesktopAccessRole.admin, models.DesktopAccessRole.member]


class DesktopAccessRevoke(BaseModel):
    access_id: UUID4


class DesktopUserAccessSet(BaseModel):
    desktop_id: UUID4
    user_id: UUID4
    role: Literal[models.DesktopAccessRole.admin, models.DesktopAccessRole.member]


class PrincipalCreate(BaseModel):
    public_key: PublicKeyHex
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + relativedelta(months=1))


class PrincipalRotate(BaseModel):
    old_public_key: PublicKeyHex
    new_public_key: PublicKeyHex


class PrincipalGet(PrincipalCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUIDStr
    created_at: DateTimeStr
    expires_at: DateTimeStr


class AppVersionUpload(BaseModel):
    name: str
    version: str
    checksum: str


class AppVersionCheck(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    name: str
    version: str
    os: models.OS
    cpu_architecture: models.CPUArchitecture


class AppVersionCheckResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    current_version: str
    latest_version: str
    os: str
    cpu_architecture: models.CPUArchitecture
    download_url: str
    asset_name: str
    checksum: str
    released_at: DateTimeStr


class AppVersionGet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUIDStr
    version: str
    checksum: str
    released_at: DateTimeStr


class DesktopBasicGet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUIDStr
    name: str


class DesktopInviteInboxGet(DesktopInviteGet):
    desktop: DesktopBasicGet


class DesktopAccessListRequest(BaseModel):
    desktop_id: UUID4


class DesktopUserAccessDetailGet(DesktopUserAccessGet):
    user: UserGet


class DesktopWithRoleGet(DesktopGet):
    role: models.DesktopAccessRole


class DesktopInviteOutboxGet(DesktopInviteGet):
    invitee_user: UserGet


class InviteCancel(BaseModel):
    invitation_id: UUID4
