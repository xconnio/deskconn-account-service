from xconn import Component
from xconn.types import Depends, CallDetails
from xconn.exception import ApplicationError
from sqlalchemy.ext.asyncio import AsyncSession

from deskconn import schemas, uris, helpers
from deskconn.database.database import get_database
from deskconn.database.backend import user as user_backend

component = Component()


@component.register("io.xconn.deskconn.coturn.credentials.create", response_model=schemas.CoturnCredentials)
async def generate_coturn_credentials(details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{details.authid}' not found")

    return helpers.generate_coturn_credentials(db_user.id)
