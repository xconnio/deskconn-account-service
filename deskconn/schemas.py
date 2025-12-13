from pydantic import BaseModel, ConfigDict

from deskconn import helpers
from deskconn.models import UserRole


class User(BaseModel):
    email: str
    name: str
    role: UserRole


class UserCreate(User):
    password: str


class UserVerify(BaseModel):
    email: str
    code: str


class UserGet(User):
    model_config = ConfigDict(from_attributes=True)

    id: int


class CRAUser(UserGet):
    model_config = ConfigDict(from_attributes=True)

    salt: str
    password: str
    authrole: str = helpers.ROLE_USER
    iterations: int = helpers.ITERATIONS
    key_length: int = helpers.KEY_LENGTH


class DeviceCreate(BaseModel):
    device_id: str
    public_key: str
    name: str | None = None


class DeviceGet(DeviceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
