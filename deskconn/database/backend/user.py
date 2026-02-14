from uuid import UUID
from typing import Any

from sqlalchemy import select, exists, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from deskconn import models, schemas, helpers
from deskconn.database.backend import device as device_backend
from deskconn.database.backend import desktop as desktop_backend
from deskconn.database.backend import organization as organization_backend


async def create_user(db: AsyncSession, data: schemas.UserCreate) -> models.User:
    data.password, salt = helpers.hash_password_and_generate_salt(data.password)
    db_user = models.User(**data.model_dump(), salt=salt)

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
    await desktop_backend.delete_user_desktop_access(db, db_user)
    await organization_backend.delete_user_invites(db, db_user)
    await organization_backend.delete_user_memberships(db, db_user)
    await desktop_backend.delete_user_desktops(db, db_user)
    await organization_backend.delete_user_organizations(db, db_user)
    await device_backend.delete_user_devices(db, db_user)

    await db.delete(db_user)
    await db.commit()


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


async def get_user_public_keys(db: AsyncSession, user_id: UUID) -> dict[str, list[str]]:
    principal_query = (
        select(models.User.email.label("authid"), models.Principal.public_key.label("public_key"))
        .join(models.User, models.User.id == models.Principal.user_id)
        .where(models.Principal.user_id == user_id)
    )

    device_query = (
        select(models.User.email.label("authid"), models.Device.public_key.label("public_key"))
        .join(models.User, models.User.id == models.Device.user_id)
        .where(models.Device.user_id == user_id)
    )

    desktop_query = select(models.Desktop.authid.label("authid"), models.Desktop.public_key.label("public_key")).where(
        models.Desktop.user_id == user_id
    )

    keys_union = union_all(principal_query, device_query, desktop_query).subquery()

    stmt = select(keys_union.c.authid, keys_union.c.public_key).distinct()
    result = await db.execute(stmt)

    authorized_keys: dict[str, list[str]] = {}

    for authid, public_key in result.all():
        authorized_keys.setdefault(authid, []).append(public_key)

    return authorized_keys
