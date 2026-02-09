import os
import base64
import secrets
import hashlib
import threading
from typing import Tuple, Any
from datetime import datetime, timezone, timedelta

import resend
from dotenv import load_dotenv
from xconn.exception import ApplicationError
from xconn.async_session import AsyncSession
from wampproto.auth.wampcra import derive_cra_key

from deskconn import uris

load_dotenv()

ITERATIONS = 1000
KEY_LENGTH = 32

ROLE_USER = "user"
ROLE_DESKTOP = "xconnio:deskconn:desktop:{authid}"
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5

CLOUD_REALM = "io.xconn.deskconn"
TOPIC_DESKTOP_DETACH = "io.xconn.deskconn.desktop.{machine_id}.detach"
RPC_KILL_SESSION = "wamp.session.kill_by_authid"
TOPIC_KEY_ADD = "io.xconn.deskconn.desktop.{machine_id}.key.add"
TOPIC_KEY_REMOVE = "io.xconn.deskconn.desktop.{machine_id}.key.remove"

RESEND_API_KEY = os.getenv("RESEND_API_KEY", None)
if RESEND_API_KEY is None or RESEND_API_KEY == "":
    raise ValueError("'RESEND_API_KEY' missing in environment variables.")

resend.api_key = RESEND_API_KEY


def utcnow():
    return datetime.now(timezone.utc)


def hash_password_and_generate_salt(password: str) -> Tuple[str, str]:
    salt = generate_salt()

    return hash_password(password, salt), salt


def hash_password(password: str, salt: str) -> str:
    return derive_cra_key(salt, password, ITERATIONS, KEY_LENGTH).decode()


def verify_password(password: str, salt: str, hashed_password: str) -> bool:
    return hash_password(password, salt) == hashed_password


def generate_salt(length: int = 16) -> str:
    salt_bytes = os.urandom(length)

    return base64.b64encode(salt_bytes).decode("utf-8")


def generate_email_otp() -> str:
    return f"{secrets.randbelow(10**OTP_LENGTH):0{OTP_LENGTH}d}"


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def otp_expiry_time() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)


def generate_and_send_otp(email: str) -> Tuple[str, datetime]:
    otp = generate_email_otp()
    otp_hash = hash_otp(otp)
    otp_expires_at = otp_expiry_time()
    send_user_verification_email(email, otp)

    return otp_hash, otp_expires_at


def verify_email_otp(stored_hash: str | None, expires_at: datetime | None, provided_code: str) -> bool:
    if stored_hash is None or expires_at is None:
        return False

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if utcnow() > expires_at:
        return False

    return hash_otp(provided_code) == stored_hash


def send_user_verification_email(user_email: str, code: str) -> None:
    params: resend.Emails.SendParams = {
        "from": "Deskconn <noreply@deskconn.com>",
        "to": [user_email],
        "subject": "Deskconn Verification Code",
        "text": f"Your verification code is: {code}",
    }

    thread = threading.Thread(target=send_email, args=(params,))
    thread.start()


def send_email(params: resend.Emails.SendParams) -> None:
    try:
        resend.Emails.send(params)
    except Exception as e:
        print("Failed to send email, reason:", e)


def send_organization_invite_email(inviter: str, invitee: str):
    params: resend.Emails.SendParams = {
        "from": "Deskconn <noreply@deskconn.com>",
        "to": [invitee],
        "subject": "Organization Invitation",
        "text": f"You have been invited to join the {inviter}'s organization.",
    }

    thread = threading.Thread(target=send_email, args=(params,))
    thread.start()


async def call_cloud_router_rpc(session: AsyncSession, uri: str, args: list[Any], error_message: str) -> None:
    try:
        await session.call(uri, args)
    except ApplicationError as app_err:
        raise ApplicationError(uris.ERROR_INTERNAL_ERROR, f"{error_message}. Error is: {app_err.args}")
    except Exception as err:
        raise ApplicationError(uris.ERROR_INTERNAL_ERROR, str(err))
