from xconn import Component
from xconn.types import Depends, CallDetails
from xconn.exception import ApplicationError
from sqlalchemy.ext.asyncio import AsyncSession

from deskconn import schemas, uris, helpers
from deskconn.database.database import get_database
from deskconn.database.backend import user as user_backend
from deskconn.database.backend import desktop as desktop_backend

component = Component()

COTURN_URLS = [
    "turns:turn.deskconn.com:5349?transport=tcp",
    "turn:turn.deskconn.com:3478?transport=tcp",
    "turn:turn.deskconn.com:3478?transport=udp",
]


@component.register("io.xconn.deskconn.coturn.credentials.create")
async def generate_coturn_credentials(details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        db_desktop = await desktop_backend.get_desktop_by_authid(db, details.authid)
        if db_desktop is None:
            raise ApplicationError(uris.ERROR_NOT_FOUND, f"User/Desktop with authid '{details.authid}' not found")
        user_id = db_desktop.id
    else:
        user_id = db_user.id

    creds = helpers.generate_coturn_credentials(user_id)

    return schemas.CoturnCredentials(
        username=creds.username, credential=creds.credential, expires_at=creds.expires_at, urls=COTURN_URLS
    ).model_dump()
