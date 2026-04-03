from uuid import UUID

from sqlalchemy.orm import joinedload
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from deskconn import models, schemas


async def get_app_by_name(db: AsyncSession, name: str) -> models.App | None:
    stmt = select(models.App).where(models.App.name == name)
    result = await db.execute(stmt)

    return result.scalar()


async def create_app(db: AsyncSession, name: str) -> models.App:
    app = models.App(name=name)
    db.add(app)
    await db.commit()
    await db.refresh(app)

    return app


async def app_version_exists(db: AsyncSession, app_id: UUID, version: str) -> bool:
    stmt = select(exists().where(models.AppVersion.app_id == app_id, models.AppVersion.version == version))
    result = await db.execute(stmt)

    return bool(result.scalar())


async def create_app_version(db: AsyncSession, app: models.App, data: schemas.AppVersionUpload) -> models.AppVersion:
    app_version = models.AppVersion(
        app_id=app.id,
        version=data.version,
        checksum=data.checksum,
    )

    app.last_updated = app_version.released_at

    db.add(app_version)
    await db.commit()

    return app_version


async def get_latest_app_version(db: AsyncSession, app_id) -> models.AppVersion | None:
    stmt = (
        select(models.AppVersion)
        .where(models.AppVersion.app_id == app_id)
        .options(joinedload(models.AppVersion.app))
        .order_by(models.AppVersion.released_at.desc())
    )
    result = await db.execute(stmt)

    return result.scalar()
