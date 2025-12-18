from typing import Any
from uuid import UUID

from sqlalchemy import select, Sequence, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from deskconn import models, schemas


async def create_organization(
    db: AsyncSession,
    user: models.User,
    data: schemas.OrganizationCreate,
) -> models.Organization:
    db_organization = models.Organization(name=data.name, owner_id=user.id)

    db_organization.members.append(
        models.OrganizationMember(user_id=user.id, role=models.OrganizationRole.owner, all_desktops=True)
    )

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
