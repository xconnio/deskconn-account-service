from xconn import Component
from xconn.exception import ApplicationError
from sqlalchemy.ext.asyncio import AsyncSession
from xconn.types import Depends, CallDetails

from deskconn import schemas, uris
from deskconn.database.database import get_database
from deskconn.database.backend import user as user_backend

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


@component.register("io.xconn.deskconn.account.cra.verify", response_model=schemas.CRAUser)
async def verify_cra(authid: str, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{authid}' not found")

    return db_user
