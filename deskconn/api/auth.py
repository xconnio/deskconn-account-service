from xconn import Component
from xconn.exception import ApplicationError
from sqlalchemy.ext.asyncio import AsyncSession
from xconn.types import Depends, Result

from deskconn import schemas, uris, helpers
from deskconn.database.database import get_database
from deskconn.database.backend import user as user_backend
from deskconn.database.backend import device as device_backend
from deskconn.database.backend import desktop as desktop_backend
from deskconn.database.backend import organization as organization_backend

component = Component()


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
    if db_user is not None:
        if not db_user.is_verified:
            raise ApplicationError(uris.ERROR_USER_NOT_VERIFIED, f"User with authid '{authid}' is not verified")

        db_device = await device_backend.get_device_by_public_key(db, public_key, db_user.id)
        if db_device is None:
            raise ApplicationError(uris.ERROR_DEVICE_NOT_FOUND, f"Device with public key '{public_key}' not found")

        authrole = helpers.ROLE_USER
    else:
        db_desktop = await desktop_backend.get_desktop_by_public_key(db, authid, public_key)
        if db_desktop is None:
            raise ApplicationError(
                uris.ERROR_DEVICE_NOT_FOUND, f"Desktop with authid '{authid}' public key '{public_key}' not found"
            )

        authrole = helpers.ROLE_DESKTOP

    return Result(args=[{"authid": authid, "authrole": authrole}])


@component.register("io.xconn.deskconn.desktop.access")
async def desktop_access(authid: str, desktop_authid: str, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{authid}' not found")

    if not db_user.is_verified:
        raise ApplicationError(uris.ERROR_USER_NOT_VERIFIED, f"User with authid '{authid}' is not verified")

    db_desktop = await desktop_backend.get_desktop_by_authid(db, desktop_authid)
    if db_desktop is None:
        raise ApplicationError(uris.ERROR_DEVICE_NOT_FOUND, f"Desktop with authid '{desktop_authid}' not found")

    if await organization_backend.get_organization_membership(db, db_desktop.organization_id, db_user) is None:
        raise ApplicationError(
            uris.ERROR_USER_NOT_AUTHORIZED, f"User with authid '{authid}' is not authorized to access desktop"
        )

    return None
