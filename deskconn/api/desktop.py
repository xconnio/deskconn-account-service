from xconn import Component, uris as xconn_uris
from xconn.exception import ApplicationError
from sqlalchemy.ext.asyncio import AsyncSession
from xconn.types import Depends, CallDetails

from deskconn import schemas, uris
from deskconn.database.database import get_database
from deskconn.database.backend import user as user_backend
from deskconn.database.backend import desktop as desktop_backend

component = Component()


@component.register("io.xconn.deskconn.desktop.attach", response_model=schemas.DesktopGet)
async def create(rs: schemas.DesktopCreate, details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{details.authid}' not found")

    if await desktop_backend.desktop_exists_by_authid(db, rs.authid):
        raise ApplicationError(uris.ERROR_DESKTOP_EXISTS, f"Desktop with device id '{rs.authid}' already exists")

    return await desktop_backend.create_desktop(db, rs, db_user)


@component.register("io.xconn.deskconn.desktop.list", response_model=schemas.DesktopGet)
async def list_desktops(details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{details.authid}' not found")

    return await desktop_backend.get_user_desktops(db, db_user.id)


@component.register("io.xconn.deskconn.desktop.update", response_model=schemas.DesktopGet)
async def update(rs: schemas.DesktopUpdate, details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{details.authid}' not found")

    data = rs.model_dump(exclude_none=True)
    data.pop("id", None)
    if len(data) == 0:
        raise ApplicationError(xconn_uris.ERROR_INVALID_ARGUMENT, "No field to update")

    db_desktop = await desktop_backend.get_user_desktop_by_id(db, rs.id, db_user)
    if db_desktop is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"Desktop with id '{rs.id}' not found")

    return await desktop_backend.update_desktop(db, db_desktop, data)


@component.register("io.xconn.deskconn.desktop.delete")
async def delete(rs: schemas.DesktopDelete, details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{details.authid}' not found")

    db_desktop = await desktop_backend.get_user_desktop_by_id(db, rs.id, db_user)
    if db_desktop is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"Desktop with id '{rs.id}' not found")

    await desktop_backend.delete_desktop(db, db_desktop)
