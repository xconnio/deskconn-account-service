from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from deskconn import models, schemas, helpers


async def create_user(db: AsyncSession, data: schemas.UserCreate) -> models.User:
    salt = helpers.generate_salt()
    data.password = helpers.hash_password(data.password, salt)
    db_user = models.User(**data.model_dump(), salt=salt)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


async def get_user_by_id(db: AsyncSession, user_id: int) -> models.User | None:
    stmt = select(models.User).where(models.User.id == user_id)
    result = await db.execute(stmt)

    return result.scalar()


async def get_user_by_email(db: AsyncSession, email: str) -> models.User | None:
    stmt = select(models.User).where(models.User.email == email)
    result = await db.execute(stmt)

    return result.scalar()
