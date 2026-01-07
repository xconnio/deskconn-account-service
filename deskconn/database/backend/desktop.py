from uuid import UUID
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists, Sequence

from deskconn import models, schemas


async def create_desktop(db: AsyncSession, data: schemas.DesktopCreate, user: models.User) -> models.Desktop:
    db_desktop = models.Desktop(**data.model_dump(), user_id=user.id)
    db.add(db_desktop)
    await db.commit()
    await db.refresh(db_desktop)

    return db_desktop


async def desktop_exists_by_authid(db: AsyncSession, authid: str) -> bool:
    stmt = select(exists().where(models.Desktop.authid == authid))
    result = await db.execute(stmt)

    return bool(result.scalar())


async def get_user_desktops(db: AsyncSession, user_id: int) -> Sequence[models.Desktop]:
    stmt = select(models.Desktop).where(models.Desktop.user_id == user_id)
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
    await db.delete(db_desktop)
    await db.commit()


async def get_desktop_by_public_key(db: AsyncSession, authid: str, public_key: str) -> models.Device | None:
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
    db: AsyncSession, desktop_id: UUID, member_id: UUID, data: schemas.DesktopAccessGrant
) -> models.DesktopAccess:
    db_desktop_access = models.DesktopAccess(desktop_id=desktop_id, member_id=member_id, role=data.role)
    db.add(db_desktop_access)
    await db.commit()
    await db.refresh(db_desktop_access)

    return db_desktop_access
