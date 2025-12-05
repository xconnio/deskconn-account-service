from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists, Sequence, or_

from deskconn import models, schemas


async def device_exists_by_keys(db: AsyncSession, rs: schemas.DeviceCreate) -> bool:
    stmt = select(
        exists().where(or_(models.Device.public_key == rs.public_key, models.Device.device_id == rs.device_id))
    )
    result = await db.execute(stmt)

    return bool(result.scalar())


async def create_device(db: AsyncSession, data: schemas.DeviceCreate, user: models.User) -> models.Device:
    db_device = models.Device(**data.model_dump(), user_id=user.id)
    db.add(db_device)
    await db.commit()
    await db.refresh(db_device)

    return db_device


async def get_user_public_keys(db: AsyncSession, user_id: int) -> Sequence[models.Device]:
    stmt = select(models.Device).where(models.Device.user_id == user_id)
    result = await db.execute(stmt)

    return result.scalars().all()


async def get_device_by_public_key(db: AsyncSession, public_key: str, user_id: int) -> models.Device | None:
    stmt = select(models.Device).where(models.Device.public_key == public_key).where(models.Device.user_id == user_id)
    result = await db.execute(stmt)

    return result.scalar()
