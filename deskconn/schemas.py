from typing import Annotated

from pydantic import BaseModel, ConfigDict, UUID4, PlainSerializer, StringConstraints

from deskconn import helpers
from deskconn.models import UserRole

# serialize UUID as string for JSON responses
UUIDStr = Annotated[UUID4, PlainSerializer(lambda v: str(v), return_type=str)]

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
    desktop_id: str
    public_key: PublicKeyHex
    name: str | None = None


class DesktopGet(DesktopCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUIDStr


class DesktopDelete(BaseModel):
    id: UUID4


class DesktopUpdate(DesktopDelete):
    public_key: PublicKeyHex | None = None
    name: str | None = None
