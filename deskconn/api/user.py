from xconn import Component
from xconn.exception import ApplicationError
from sqlalchemy.ext.asyncio import AsyncSession
from xconn.types import Depends, CallDetails, Result

from deskconn import schemas, uris, helpers
from deskconn.database.database import get_database
from deskconn.database.backend import user as user_backend
from deskconn.database.backend import device as device_backend

component = Component()


@component.register("io.xconn.deskconn.account.create", response_model=schemas.UserGet)
async def create(rs: schemas.UserCreate, db: AsyncSession = Depends(get_database)):
    if await user_backend.get_user_by_email(db, rs.email) is not None:
        raise ApplicationError(uris.ERROR_USER_EXISTS, f"User with email '{rs.email}' already exists")

    return await user_backend.create_user(db, rs)


@component.register("io.xconn.deskconn.account.get", response_model=schemas.UserGet)
async def get(details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{details.authid}' not found")

    return db_user


@component.register("io.xconn.deskconn.account.verify")
async def account_verification(rs: schemas.UserVerify, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, rs.email)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with email '{rs.email}' not found")

    if db_user.is_verified:
        raise ApplicationError(uris.ERROR_USER_ALREADY_VERIFIED, "User is already verified")

    if not helpers.verify_email_otp(db_user.otp_hash, db_user.otp_expires_at, rs.code):
        raise ApplicationError(uris.ERROR_USER_OTP_INVALID, "OTP invalid or expired")

    await user_backend.verify_user(db, db_user)


@component.register("io.xconn.deskconn.account.otp.resend")
async def otp_resend(email: str, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, email)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with email '{email}' not found")

    if db_user.is_verified:
        raise ApplicationError(uris.ERROR_USER_ALREADY_VERIFIED, "User is already verified")

    await user_backend.generate_and_save_otp(db, db_user)


@component.register("io.xconn.deskconn.account.cra.verify", response_model=schemas.CRAUser)
async def verify_cra(authid: str, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{authid}' not found")

    if not db_user.is_verified:
        raise ApplicationError(uris.ERROR_USER_NOT_VERIFIED, f"User with authid '{authid}' is not verified")

    return db_user


@component.register("io.xconn.deskconn.account.cryptosign.verify")
async def verify_cryptosign(authid: str, public_key: str, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{authid}' not found")

    if not db_user.is_verified:
        raise ApplicationError(uris.ERROR_USER_NOT_VERIFIED, f"User with authid '{authid}' is not verified")

    db_device = await device_backend.get_device_by_public_key(db, public_key, db_user.id)
    if db_device is None:
        raise ApplicationError(uris.ERROR_DEVICE_NOT_FOUND, f"Device with public key '{public_key}' not found")

    return Result(args=[{"authid": authid, "authrole": helpers.ROLE_USER}])
