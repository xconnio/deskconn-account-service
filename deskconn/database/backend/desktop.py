from uuid import UUID
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists, Sequence, delete

from deskconn import models, schemas


async def create_desktop(
    db: AsyncSession,
    data: schemas.DesktopCreate,
    user: models.User,
    org_membership: models.OrganizationMember,
    realm: str,
) -> models.Desktop:
    db_desktop = models.Desktop(**data.model_dump(), user_id=user.id, realm=realm)
    db.add(db_desktop)
    await db.commit()
    await db.refresh(db_desktop)

    await grant_access_to_desktop(db, db_desktop.id, org_membership.id, models.OrganizationRole.owner)

    return db_desktop


async def desktop_exists_by_authid(db: AsyncSession, authid: str) -> bool:
    stmt = select(exists().where(models.Desktop.authid == authid))
    result = await db.execute(stmt)

    return bool(result.scalar())


async def get_user_desktops(db: AsyncSession, user_id: int) -> Sequence[models.Desktop]:
    stmt = (
        select(models.Desktop)
        .join(models.Desktop.accesses)
        .join(models.DesktopAccess.member)
        .where(models.OrganizationMember.user_id == user_id)
        .distinct()
    )

    result = await db.execute(stmt)

    return result.scalars().all()


async def get_user_desktop_by_id(db: AsyncSession, desktop_id: UUID, db_user: models.User) -> models.Desktop:
    stmt = select(models.Desktop).where(models.Desktop.id == desktop_id).where(models.Desktop.user_id == db_user.id)
    result = await db.execute(stmt)

    return result.scalar()


async def get_desktop_by_id(db: AsyncSession, desktop_id: UUID) -> models.Desktop:
    stmt = select(models.Desktop).where(models.Desktop.id == desktop_id)
    result = await db.execute(stmt)

    return result.scalar()


async def update_desktop(db: AsyncSession, db_desktop: models.Desktop, data: dict[str, Any]) -> models.Desktop:
    for field, value in data.items():
        if hasattr(db_desktop, field):
            setattr(db_desktop, field, value)

    db.add(db_desktop)
    await db.commit()
    await db.refresh(db_desktop)

    return db_desktop


async def delete_desktop(db: AsyncSession, db_desktop: models.Desktop) -> None:
    await remove_desktop_access(db, db_desktop.id)
    await db.delete(db_desktop)
    await db.commit()


async def get_desktop_by_public_key(db: AsyncSession, authid: str, public_key: str) -> models.Desktop | None:
    stmt = select(models.Desktop).where(models.Desktop.authid == authid).where(models.Desktop.public_key == public_key)
    result = await db.execute(stmt)

    return result.scalar()


async def desktop_access_exists(db: AsyncSession, desktop_id: UUID, member_id: UUID) -> bool:
    stmt = select(
        exists().where(models.DesktopAccess.desktop_id == desktop_id).where(models.DesktopAccess.member_id == member_id)
    )
    result = await db.execute(stmt)

    return bool(result.scalar())


async def grant_access_to_desktop(
    db: AsyncSession, desktop_id: UUID, member_id: UUID, role: models.OrganizationRole
) -> models.DesktopAccess:
    db_desktop_access = models.DesktopAccess(desktop_id=desktop_id, member_id=member_id, role=role)
    db.add(db_desktop_access)
    await db.commit()
    await db.refresh(db_desktop_access)

    return db_desktop_access


async def get_desktop_by_authid(db: AsyncSession, desktop_authid: str) -> models.Desktop:
    stmt = select(models.Desktop).where(models.Desktop.authid == desktop_authid)
    result = await db.execute(stmt)

    return result.scalar()


async def get_desktop_by_realm(db: AsyncSession, realm: str) -> models.Desktop:
    stmt = select(models.Desktop).where(models.Desktop.realm == realm)
    result = await db.execute(stmt)

    return result.scalar()


async def remove_desktop_access(db: AsyncSession, desktop_id: UUID) -> None:
    stmt = delete(models.DesktopAccess).where(models.DesktopAccess.desktop_id == desktop_id)
    await db.execute(stmt)


async def delete_user_desktop_access(db: AsyncSession, db_user: models.User) -> None:
    subq = select(models.OrganizationMember.id).where(models.OrganizationMember.user_id == db_user.id)
    stmt = delete(models.DesktopAccess).where(models.DesktopAccess.member_id.in_(subq))
    await db.execute(stmt)


async def delete_user_desktops(db: AsyncSession, db_user: models.User) -> None:
    stmt = delete(models.Desktop).where(models.Desktop.user_id == db_user.id)
    await db.execute(stmt)
