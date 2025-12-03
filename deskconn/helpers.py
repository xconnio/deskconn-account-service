import os
import base64
from datetime import datetime, timezone

from wampproto.auth.wampcra import derive_cra_key

ITERATIONS = 1000
KEY_LENGTH = 32

ROLE_USER = "user"


def utcnow():
    return datetime.now(timezone.utc)


def hash_password(password: str, salt: str) -> str:
    return derive_cra_key(salt, password, ITERATIONS, KEY_LENGTH).decode()


def verify_password(password: str, salt: str, hashed_password: str) -> bool:
    return hash_password(password, salt) == hashed_password


def generate_salt(length: int = 16) -> str:
    salt_bytes = os.urandom(length)

    return base64.b64encode(salt_bytes).decode("utf-8")
