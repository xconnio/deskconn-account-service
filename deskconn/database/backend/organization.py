from typing import Any
from uuid import UUID
from datetime import timedelta

from sqlalchemy import select, Sequence, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from deskconn import models, schemas, helpers


async def create_organization(
    db: AsyncSession,
    user: models.User,
    data: schemas.OrganizationCreate,
) -> models.Organization:
    db_organization = models.Organization(name=data.name, owner_id=user.id)

    db_organization.members.append(models.OrganizationMember(user_id=user.id, role=models.OrganizationRole.owner))

    db.add(db_organization)
    await db.commit()
    await db.refresh(db_organization)

    return db_organization


async def get_user_organization(
    db: AsyncSession,
    organization_id: UUID,
) -> models.Organization | None:
    stmt = (
        select(models.Organization)
        .where(models.Organization.id == organization_id)
        .options(
            joinedload(models.Organization.members).joinedload(models.OrganizationMember.user),
            joinedload(models.Organization.owner),
        )
    )

    result = await db.execute(stmt)

    return result.unique().scalar_one_or_none()


async def list_user_organizations(db: AsyncSession, user: models.User) -> Sequence[models.Organization]:
    stmt = (
        select(models.Organization).join(models.OrganizationMember).where(models.OrganizationMember.user_id == user.id)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


async def update_organization(
    db: AsyncSession, organization: models.Organization, data: dict[str, Any]
) -> models.Organization:
    for field, value in data.items():
        if hasattr(organization, field):
            setattr(organization, field, value)

    db.add(organization)
    await db.commit()
    await db.refresh(organization)

    return organization


async def delete_organization(db: AsyncSession, db_organization: models.Organization) -> None:
    await delete_organization_members(db, db_organization.id)
    await db.delete(db_organization)

    await db.commit()


async def delete_organization_members(db: AsyncSession, organization_id: UUID) -> None:
    stmt = delete(models.OrganizationMember).where(models.OrganizationMember.organization_id == organization_id)
    await db.execute(stmt)


async def get_organization_by_id(db: AsyncSession, organization_id: UUID) -> models.Organization | None:
    stmt = select(models.Organization).where(models.Organization.id == organization_id)
    result = await db.execute(stmt)

    return result.scalar()


async def get_owner_organization_by_id(
    db: AsyncSession, organization_id: UUID, user_id: int
) -> models.Organization | None:
    stmt = (
        select(models.Organization)
        .where(models.Organization.id == organization_id)
        .where(models.Organization.owner_id == user_id)
    )
    result = await db.execute(stmt)

    return result.scalar()


async def get_organization_membership(
    db: AsyncSession, organization_id: UUID, db_user: models.User
) -> models.OrganizationMember | None:
    stmt = (
        select(models.OrganizationMember)
        .where(
            models.OrganizationMember.organization_id == organization_id,
            models.OrganizationMember.user_id == db_user.id,
        )
        .options(joinedload(models.OrganizationMember.organization))
    )
    result = await db.execute(stmt)

    return result.scalar()


async def create_invite(
    db: AsyncSession,
    user: models.User,
    organization: models.Organization,
    data: schemas.OrganizationInviteCreate,
    invitee: models.User,
) -> models.OrganizationInvite:
    db_org_invitation = models.OrganizationInvite(
        inviter_id=user.id,
        organization_id=organization.id,
        role=data.role,
        status=models.InvitationStatus.pending,
        expires_at=helpers.utcnow() + timedelta(hours=data.expires_in_hours),
        invitee_id=invitee.id,
    )

    db.add(db_org_invitation)
    await db.commit()
    await db.refresh(db_org_invitation)

    helpers.send_organization_invite_email(user.email, invitee.email)

    return db_org_invitation


async def get_organization_invitation(
    db: AsyncSession, organization_id: UUID, invitee_id: int
) -> models.OrganizationInvite | None:
    stmt = select(models.OrganizationInvite).where(
        models.OrganizationInvite.organization_id == organization_id,
        models.OrganizationInvite.invitee_id == invitee_id,
        models.OrganizationInvite.expires_at > helpers.utcnow(),
    )
    result = await db.execute(stmt)

    return result.scalar()


async def get_organization_invitation_by_id(db: AsyncSession, invitation_id: UUID) -> models.OrganizationInvite | None:
    stmt = select(models.OrganizationInvite).where(models.OrganizationInvite.id == invitation_id)
    result = await db.execute(stmt)

    return result.scalar()


async def change_invitation_status(
    db: AsyncSession, invitation: models.OrganizationInvite, status: models.InvitationStatus
) -> None:
    invitation.status = status
    await db.commit()


async def respond_to_invitation(
    db: AsyncSession, invitation: models.OrganizationInvite, status: models.InvitationStatus
) -> models.OrganizationMember | None:
    await change_invitation_status(db, invitation, status)

    if status == models.InvitationStatus.accepted:
        db_organization_member = models.OrganizationMember(
            role=invitation.role,
            organization_id=invitation.organization_id,
            user_id=invitation.invitee_id,
        )

        db.add(db_organization_member)
        await db.commit()
        await db.refresh(db_organization_member)

        return db_organization_member


async def list_inbox_invitation(db: AsyncSession, user: models.User) -> Sequence[models.OrganizationInvite]:
    stmt = select(models.OrganizationInvite).where(models.OrganizationInvite.invitee_id == user.id)

    result = await db.execute(stmt)
    return result.scalars().all()


async def list_outbox_invitation(db: AsyncSession, user: models.User) -> Sequence[models.OrganizationInvite]:
    stmt = select(models.OrganizationInvite).where(models.OrganizationInvite.inviter_id == user.id)

    result = await db.execute(stmt)
    return result.scalars().all()
