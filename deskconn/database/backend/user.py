from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from deskconn import models, schemas, helpers


async def create_user(db: AsyncSession, data: schemas.UserCreate) -> models.User:
    salt = helpers.generate_salt()
    data.password = helpers.hash_password(data.password, salt)
    db_user = models.User(**data.model_dump(), salt=salt)

    # guest users are allowed to call the APIs
    if db_user.role == models.UserRole.guest:
        db_user.is_verified = True
    else:
        otp = helpers.generate_email_otp()
        db_user.otp_hash = helpers.hash_otp(otp)
        db_user.otp_expires_at = helpers.otp_expiry_time()
        helpers.send_user_verification_email(db_user.email, otp)

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


async def verify_user(db: AsyncSession, db_user: models.User) -> None:
    db_user.is_verified = True
    await db.commit()
