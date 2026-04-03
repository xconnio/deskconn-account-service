from xconn import Component
from xconn.types import Depends
from xconn.exception import ApplicationError
from sqlalchemy.ext.asyncio import AsyncSession

from deskconn import helpers, schemas, uris
from deskconn.database.database import get_database
from deskconn.database.backend import update as update_backend

component = Component()


@component.register("io.xconn.deskconn.app.update.check")
async def check(rs: schemas.AppVersionCheck, db: AsyncSession = Depends(get_database)):
    app = await update_backend.get_app_by_name(db, rs.name)
    if app is None:
        raise ApplicationError(uris.ERROR_NOT_FOUND, f"App '{rs.name}' not found")

    latest_version = await update_backend.get_latest_app_version(db, app.id)
    if latest_version is None:
        raise ApplicationError(uris.ERROR_NOT_FOUND, f"No version found for app '{rs.name}'")

    if latest_version.version == rs.version:
        return None

    asset_name = helpers.release_asset_name(app.name, latest_version.version, rs.os, rs.cpu_architecture)
    download_url = helpers.release_download_url(
        helpers.DEFAULT_DESKCONN_RELEASE_BASE_URL,
        latest_version.version,
        app.name,
        rs.os,
        rs.cpu_architecture,
    )

    return schemas.AppVersionCheckResult(
        name=app.name,
        current_version=rs.version,
        latest_version=latest_version.version,
        os=rs.os,
        cpu_architecture=rs.cpu_architecture,
        download_url=download_url,
        asset_name=asset_name,
        checksum=latest_version.checksum,
        released_at=latest_version.released_at,
    ).model_dump()


@component.register("io.xconn.deskconn.app.update", response_model=schemas.AppVersionGet)
async def upload(rs: schemas.AppVersionUpload, db: AsyncSession = Depends(get_database)):
    app = await update_backend.get_app_by_name(db, rs.name)
    if app is None:
        app = await update_backend.create_app(db, rs.name)

    if await update_backend.app_version_exists(db, app.id, rs.version):
        raise ApplicationError(
            uris.ERROR_APP_VERSION_EXISTS,
            f"Version '{rs.version}' for app '{rs.name}' already exists",
        )

    return await update_backend.create_app_version(db, app, rs)
