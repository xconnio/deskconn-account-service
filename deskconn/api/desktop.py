from xconn import Component, uris as xconn_uris
from xconn.exception import ApplicationError
from sqlalchemy.ext.asyncio import AsyncSession
from xconn.types import Depends, CallDetails

from deskconn import schemas, uris, helpers
from deskconn.database.database import get_database
from deskconn.database.backend import user as user_backend
from deskconn.database.backend import desktop as desktop_backend
from deskconn.database.backend import organization as organization_backend

component = Component()

PROCEDURE_ADD_REALM = "io.xconn.deskconn.realm.add"
PROCEDURE_REMOVE_REALM = "io.xconn.deskconn.realm.remove"


@component.register("io.xconn.deskconn.desktop.attach", response_model=schemas.DesktopGet)
async def attach(rs: schemas.DesktopCreate, details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{details.authid}' not found")

    if await desktop_backend.desktop_exists_by_authid(db, rs.authid):
        raise ApplicationError(uris.ERROR_DESKTOP_EXISTS, f"Desktop with device id '{rs.authid}' already exists")

    db_organization = await organization_backend.get_owner_organization_by_id(db, rs.organization_id, db_user.id)
    if db_organization is None:
        raise ApplicationError(
            uris.ERROR_ORGANIZATION_NOT_FOUND,
            f"Organization with uuid '{rs.organization_id}' not found",
        )

    db_organization_membership = await organization_backend.get_organization_membership(db, rs.organization_id, db_user)
    if db_organization_membership is None:
        raise ApplicationError(uris.ERROR_INTERNAL_ERROR, "Organization membership not found")

    realm = f"io.xconn.deskconn.{db_organization_membership.organization_id}.{rs.authid}"

    # call router rpc to add realm
    await helpers.call_cloud_router_rpc(
        component.session, PROCEDURE_ADD_REALM, [realm], "Got error upon creating realm for desktop"
    )

    return await desktop_backend.create_desktop(db, rs, db_user, db_organization_membership, realm)


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


@component.register("io.xconn.deskconn.desktop.detach")
async def detach(rs: schemas.DesktopDetach, details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{details.authid}' not found")

    db_desktop = await desktop_backend.get_desktop_by_authid(db, rs.authid)
    if db_desktop is None:
        raise ApplicationError(uris.ERROR_DESKTOP_NOT_FOUND, f"Desktop with authid '{rs.authid}' not found")

    if db_desktop.user_id != db_user.id:
        raise ApplicationError(uris.ERROR_USER_NOT_AUTHORIZED, "Cannot detach a desktop from another user")

    # call router rpc to remove realm
    await helpers.call_cloud_router_rpc(
        component.session, PROCEDURE_REMOVE_REALM, [db_desktop.realm], "Got error upon deleting realm for desktop"
    )

    await desktop_backend.delete_desktop(db, db_desktop)


@component.register("io.xconn.deskconn.desktop.access.grant", response_model=schemas.DesktopAccessGet)
async def access(rs: schemas.DesktopAccessGrant, details: CallDetails, db: AsyncSession = Depends(get_database)):
    inviter = await user_backend.get_user_by_email(db, details.authid)
    if inviter is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{details.authid}' not found")

    invitee = await user_backend.get_user_by_email(db, str(rs.invitee))
    if invitee is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with email '{rs.invitee}' not found")

    if inviter.id == invitee.id:
        raise ApplicationError(uris.ERROR_USER_NOT_AUTHORIZED, "Cannot access grant to yourself")

    db_desktop = await desktop_backend.get_desktop_by_id(db, rs.id)
    if db_desktop is None:
        raise ApplicationError(uris.ERROR_DESKTOP_NOT_FOUND, f"Desktop with id '{rs.id}' not found")

    db_organization_membership = await organization_backend.get_organization_membership(
        db, db_desktop.organization_id, invitee
    )
    if db_organization_membership is None:
        raise ApplicationError(
            uris.ERROR_ORGANIZATION_NOT_FOUND,
            f"Membership for organization with uuid '{db_desktop.organization_id}' not found",
        )

    if db_organization_membership.organization.owner_id != inviter.id:
        raise ApplicationError(uris.ERROR_USER_NOT_AUTHORIZED, "User is not authorized to access this organization")

    if await desktop_backend.desktop_access_exists(db, db_desktop.id, db_organization_membership.id):
        raise ApplicationError(uris.ERROR_USER_ALREADY_MEMBER, "User already has access to this desktop")

    return await desktop_backend.grant_access_to_desktop(db, db_desktop.id, db_organization_membership.id, rs.role)


@component.register("io.xconn.deskconn.desktop.access.key.list")
async def access_keys(details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_desktop = await desktop_backend.get_desktop_by_authid(db, details.authid)
    if db_desktop is None:
        raise ApplicationError(uris.ERROR_DESKTOP_NOT_FOUND, f"Desktop with authid '{details.authid}' not found")

    return await desktop_backend.get_desktop_access_public_keys(db, db_desktop.id)
