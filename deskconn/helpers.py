import os
import base64
import secrets
import hashlib
import smtplib
import threading
from typing import Tuple
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from wampproto.auth.wampcra import derive_cra_key

load_dotenv()

ITERATIONS = 1000
KEY_LENGTH = 32

ROLE_USER = "user"
ROLE_DESKTOP = "desktop"
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5

DESKCONN_EMAIL = os.getenv("DESKCONN_EMAIL", None)
if DESKCONN_EMAIL is None or DESKCONN_EMAIL == "":
    raise ValueError("'DESKCONN_EMAIL' missing in environment variables.")

DESKCONN_PASSWORD = os.getenv("DESKCONN_PASSWORD", None)
if DESKCONN_PASSWORD is None or DESKCONN_PASSWORD == "":
    raise ValueError("'DESKCONN_PASSWORD' missing in environment variables.")


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
    msg = MIMEText(f"Your verification code is: {code}")
    msg["Subject"] = "Deskconn Verification Code"
    msg["From"] = DESKCONN_EMAIL
    msg["To"] = user_email
    thread = threading.Thread(target=send_email, args=(msg,))
    thread.start()


def send_email(msg: MIMEText) -> None:
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(DESKCONN_EMAIL, DESKCONN_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print("Failed to send email, reason:", e)


def send_organization_invite_email(inviter: str, invitee: str):
    msg = MIMEText(f"You have been invited to join the {inviter}'s organization.")
    msg["Subject"] = "Organization Invitation"
    msg["From"] = DESKCONN_EMAIL
    msg["To"] = invitee
    thread = threading.Thread(target=send_email, args=(msg,))
    thread.start()
