from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists, Sequence, delete

from deskconn import models, schemas


async def create_principal(db: AsyncSession, data: schemas.PrincipalCreate, user: models.User) -> models.Principal:
    db_principal = models.Principal(**data.model_dump(), user_id=user.id)
    db.add(db_principal)
    await db.commit()
    await db.refresh(db_principal)

    return db_principal


async def principal_exists_by_public_key(db: AsyncSession, public_key: str) -> bool:
    stmt = select(exists().where(models.Principal.public_key == public_key))
    result = await db.execute(stmt)

    return bool(result.scalar())


async def list_principals(db: AsyncSession, user: models.User) -> Sequence[models.Device]:
    stmt = select(models.Principal).where(models.Principal.user_id == user.id)
    result = await db.execute(stmt)

    return result.scalars().all()


async def delete_principal(db: AsyncSession, rs: schemas.PrincipalCreate, user: models.User) -> None:
    stmt = (
        delete(models.Principal)
        .where(models.Principal.public_key == rs.public_key)
        .where(models.Principal.user_id == user.id)
    )
    await db.execute(stmt)
    await db.commit()
