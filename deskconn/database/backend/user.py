from typing import Any

from sqlalchemy import select, exists, delete
from sqlalchemy.ext.asyncio import AsyncSession

from deskconn import models, schemas, helpers


async def create_user(db: AsyncSession, data: schemas.UserCreate) -> models.User:
    data.password, salt = helpers.hash_password_and_generate_salt(data.password)
    db_user = models.User(**data.model_dump(), salt=salt)

    # guest users are allowed to call the APIs
    if db_user.role == models.UserRole.guest:
        db_user.is_verified = True
    else:
        await generate_and_save_otp(db, db_user)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


async def update_user(db: AsyncSession, db_user: models.User, data: dict[str, Any]) -> models.User:
    for field, value in data.items():
        if field == "password":
            db_user.password, db_user.salt = helpers.hash_password_and_generate_salt(value)
            continue

        if hasattr(db_user, field):
            setattr(db_user, field, value)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


async def delete_user(db: AsyncSession, db_user: models.User) -> None:
    await delete_user_devices(db, db_user)
    await db.delete(db_user)
    await db.commit()


async def delete_user_devices(db: AsyncSession, db_user: models.User) -> None:
    stmt = delete(models.Device).where(models.Device.user_id == db_user.id)
    await db.execute(stmt)


async def guest_upgrade(db: AsyncSession, db_user: models.User, data: schemas.UserUpgrade) -> models.User:
    db_user.name = data.name
    db_user.email = data.email
    db_user.password, db_user.salt = helpers.hash_password_and_generate_salt(data.password)
    db_user.role = models.UserRole.user
    db_user.is_verified = False

    await generate_and_save_otp(db, db_user)

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


async def verify_user(db: AsyncSession, db_user: models.User) -> None:
    db_user.is_verified = True
    await db.commit()


async def generate_and_save_otp(db: AsyncSession, db_user: models.User) -> models.User:
    db_user.otp_hash, db_user.otp_expires_at = helpers.generate_and_send_otp(db_user.email)
    await db.commit()

    return db_user


async def reset_password(db: AsyncSession, db_user: models.User, new_password: str) -> models.User:
    db_user.password, db_user.salt = helpers.hash_password_and_generate_salt(new_password)
    await db.commit()

    return db_user


async def user_exists(db: AsyncSession, email: str) -> bool:
    stmt = select(exists().where(models.User.email == email))
    result = await db.execute(stmt)

    return bool(result.scalar())
