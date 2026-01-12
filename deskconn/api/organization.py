from xconn import Component, uris as xconn_uris
from xconn.exception import ApplicationError
from sqlalchemy.ext.asyncio import AsyncSession
from xconn.types import Depends, CallDetails

from deskconn import schemas, uris, models, helpers
from deskconn.database.database import get_database
from deskconn.database.backend import user as user_backend
from deskconn.database.backend import organization as organization_backend

component = Component()


@component.register("io.xconn.deskconn.organization.create", response_model=schemas.OrganizationGet)
async def create(
    rs: schemas.OrganizationCreate,
    details: CallDetails,
    db: AsyncSession = Depends(get_database),
):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{details.authid}' not found")

    return await organization_backend.create_organization(db, db_user, rs)


@component.register("io.xconn.deskconn.organization.get", response_model=schemas.OrganizationMemberList)
async def get(rs: schemas.OrganizationDelete, details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with authid '{details.authid}' not found")

    db_organization = await organization_backend.get_user_organization(db, rs.organization_id)
    if db_organization is None:
        raise ApplicationError(
            uris.ERROR_ORGANIZATION_NOT_FOUND,
            f"Organization with uuid '{rs.organization_id}' not found or access denied",
        )

    return db_organization


@component.register("io.xconn.deskconn.organization.list", response_model=schemas.OrganizationGet)
async def list_organizations(details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, "User not found")

    return await organization_backend.list_user_organizations(db, db_user)


@component.register("io.xconn.deskconn.organization.update", response_model=schemas.OrganizationGet)
async def update(
    rs: schemas.OrganizationUpdate,
    details: CallDetails,
    db: AsyncSession = Depends(get_database),
):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, "User not found")

    db_organization = await organization_backend.get_organization_by_id(db, rs.organization_id)
    if db_organization is None:
        raise ApplicationError(
            uris.ERROR_ORGANIZATION_NOT_FOUND,
            f"Organization with uuid '{rs.organization_id}' not found or access denied",
        )

    if db_organization.owner_id != db_user.id:
        raise ApplicationError(uris.ERROR_USER_NOT_AUTHORIZED, "User not authorized to delete organization")

    data = rs.model_dump(exclude_none=True)
    if len(data) == 0:
        raise ApplicationError(xconn_uris.ERROR_INVALID_ARGUMENT, "No field to update")

    return await organization_backend.update_organization(db, db_organization, data)


@component.register("io.xconn.deskconn.organization.delete")
async def delete(rs: schemas.OrganizationDelete, details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, "User not found")

    db_organization = await organization_backend.get_organization_by_id(db, rs.organization_id)
    if db_organization is None:
        raise ApplicationError(
            uris.ERROR_ORGANIZATION_NOT_FOUND,
            f"Organization with uuid '{rs.organization_id}' not found or access denied",
        )

    if db_organization.owner_id != db_user.id:
        raise ApplicationError(uris.ERROR_USER_NOT_AUTHORIZED, "User not authorized to delete organization")

    await organization_backend.delete_organization(db, db_organization)


@component.register("io.xconn.deskconn.organization.invitation.create", response_model=schemas.OrganizationInviteGet)
async def create_organization_invitation(
    rs: schemas.OrganizationInviteCreate,
    details: CallDetails,
    db: AsyncSession = Depends(get_database),
):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with email '{details.authid}' not found")

    db_organization = await organization_backend.get_organization_by_id(db, rs.organization_id)
    if db_organization is None:
        raise ApplicationError(
            uris.ERROR_ORGANIZATION_NOT_FOUND, f"Organization with uuid '{rs.organization_id}' not found"
        )

    if db_organization.owner_id != db_user.id:
        raise ApplicationError(uris.ERROR_USER_NOT_AUTHORIZED, "User not authorized to send invitations")

    if db_user.email == rs.email:
        raise ApplicationError(uris.ERROR_USER_NOT_AUTHORIZED, "Cannot send invitation to yourself")

    invitee = await user_backend.get_user_by_email(db, str(rs.email))
    if invitee is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"Invitee with email '{rs.email}' not found")

    if await organization_backend.get_organization_membership(db, db_organization.id, invitee) is not None:
        raise ApplicationError(uris.ERROR_USER_ALREADY_MEMBER, "User is already part of the organization")

    if await organization_backend.get_organization_invitation(db, db_organization.id, invitee.id) is not None:
        raise ApplicationError(
            uris.ERROR_INVITATION_ALREADY_SENT, f"Invitation already sent to user with email '{rs.email}'"
        )

    return await organization_backend.create_invite(db, db_user, db_organization, rs, invitee)


@component.register(
    "io.xconn.deskconn.organization.invitation.inbox.list", response_model=schemas.OrganizationInviteGet
)
async def list_inbox_invitation(details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with email '{details.authid}' not found")

    return await organization_backend.list_inbox_invitation(db, db_user)


@component.register(
    "io.xconn.deskconn.organization.invitation.outbox.list", response_model=schemas.OrganizationInviteGet
)
async def list_outbox_invitation(details: CallDetails, db: AsyncSession = Depends(get_database)):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with email '{details.authid}' not found")

    return await organization_backend.list_outbox_invitation(db, db_user)


@component.register("io.xconn.deskconn.organization.invitation.respond", response_model=schemas.OrganizationMemberGet)
async def respond_organization_invitation(
    rs: schemas.OrganizationInviteRespond,
    details: CallDetails,
    db: AsyncSession = Depends(get_database),
):
    db_user = await user_backend.get_user_by_email(db, details.authid)
    if db_user is None:
        raise ApplicationError(uris.ERROR_USER_NOT_FOUND, f"User with email '{details.authid}' not found")

    db_invitation = await organization_backend.get_organization_invitation_by_id(db, rs.invitation_id)
    if db_invitation is None:
        raise ApplicationError(uris.ERROR_INVITATION_NOT_FOUND, f"Invitation with id '{rs.invitation_id}' not found")

    if db_invitation.invitee_id != db_user.id:
        raise ApplicationError(uris.ERROR_USER_NOT_AUTHORIZED, "User not authorized to respond to invitations")

    if db_invitation.status != models.InvitationStatus.pending:
        raise ApplicationError(uris.ERROR_INVITATION_INVALID, "Invitation is invalid")

    # setting tzinfo to none because sqlite doesn't store timezone
    if db_invitation.expires_at < helpers.utcnow().replace(tzinfo=None):
        await organization_backend.change_invitation_status(db, db_invitation, models.InvitationStatus.expired)

        raise ApplicationError(uris.ERROR_INVITATION_EXPIRED, "Invitation is expired")

    organization_membership = await organization_backend.respond_to_invitation(db, db_invitation, rs.status)
    organization_membership.user = db_user

    return organization_membership
