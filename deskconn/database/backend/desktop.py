from uuid import UUID
from typing import Any
from datetime import timedelta

from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists, Sequence, delete, union_all, func

from deskconn import models, schemas, helpers

_ROLE_PRIORITY = {
    models.DesktopAccessRole.owner: 3,
    models.DesktopAccessRole.admin: 2,
    models.DesktopAccessRole.member: 1,
}


async def create_desktop(
    db: AsyncSession,
    data: schemas.DesktopCreate,
    user: models.User,
    realm: str,
) -> models.Desktop:
    db_desktop = models.Desktop(**data.model_dump(), user_id=user.id, realm=realm)
    db.add(db_desktop)
    await db.commit()
    await db.refresh(db_desktop)

    await grant_user_access(db, db_desktop.id, user.id, models.DesktopAccessRole.owner)

    return db_desktop


async def desktop_exists_by_authid(db: AsyncSession, authid: str) -> bool:
    stmt = select(exists().where(models.Desktop.authid == authid))
    result = await db.execute(stmt)

    return bool(result.scalar())


async def desktop_name_unique_for_user(db: AsyncSession, name: str, user_id: UUID) -> bool:
    stmt = select(exists().where(models.Desktop.name == name).where(models.Desktop.user_id == user_id))
    result = await db.execute(stmt)

    return bool(result.scalar())


async def get_user_desktops(db: AsyncSession, user_id: UUID, name: str | None = None) -> Sequence[models.Desktop]:
    accessible_ids = (
        select(models.DesktopUserAccess.desktop_id)
        .where(models.DesktopUserAccess.user_id == user_id)
        .union(
            select(models.DesktopOrganizationAccess.desktop_id)
            .join(
                models.OrganizationMember,
                models.OrganizationMember.organization_id == models.DesktopOrganizationAccess.organization_id,
            )
            .where(models.OrganizationMember.user_id == user_id)
        )
    )

    stmt = select(models.Desktop).where(models.Desktop.id.in_(accessible_ids))

    if name is not None:
        stmt = stmt.where(models.Desktop.name == name)

    result = await db.execute(stmt)

    return result.scalars().all()


async def get_user_desktops_authid_with_authrole(
    db: AsyncSession, user_id: UUID
) -> list[tuple[str, models.DesktopAccessRole]]:
    direct = (
        select(models.Desktop.authid.label("authid"), models.DesktopUserAccess.role.label("role"))
        .join(models.DesktopUserAccess, models.DesktopUserAccess.desktop_id == models.Desktop.id)
        .where(models.DesktopUserAccess.user_id == user_id)
    )

    via_org = (
        select(models.Desktop.authid.label("authid"), models.DesktopOrganizationAccess.role.label("role"))
        .join(
            models.DesktopOrganizationAccess,
            models.DesktopOrganizationAccess.desktop_id == models.Desktop.id,
        )
        .join(
            models.OrganizationMember,
            models.OrganizationMember.organization_id == models.DesktopOrganizationAccess.organization_id,
        )
        .where(models.OrganizationMember.user_id == user_id)
    )

    stmt = union_all(direct, via_org)
    result = await db.execute(stmt)

    # Deduplicate keeping the highest role per authid
    best: dict[str, models.DesktopAccessRole] = {}
    for authid, role in result.all():
        if authid not in best or _ROLE_PRIORITY[role] > _ROLE_PRIORITY[best[authid]]:
            best[authid] = role

    return list(best.items())


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


async def get_desktop_by_public_key(db: AsyncSession, authid: str, public_key: str) -> models.Desktop | None:
    stmt = select(models.Desktop).where(models.Desktop.authid == authid).where(models.Desktop.public_key == public_key)
    result = await db.execute(stmt)

    return result.scalar()


async def get_desktop_by_authid(db: AsyncSession, desktop_authid: str) -> models.Desktop:
    stmt = select(models.Desktop).where(models.Desktop.authid == desktop_authid)
    result = await db.execute(stmt)

    return result.scalar()


async def get_desktop_by_realm(db: AsyncSession, realm: str) -> models.Desktop:
    stmt = select(models.Desktop).where(models.Desktop.realm == realm)
    result = await db.execute(stmt)

    return result.scalar()


# --- User access ---

async def user_access_exists(db: AsyncSession, desktop_id: UUID, user_id: UUID) -> bool:
    stmt = select(
        exists()
        .where(models.DesktopUserAccess.desktop_id == desktop_id)
        .where(models.DesktopUserAccess.user_id == user_id)
    )
    result = await db.execute(stmt)

    return bool(result.scalar())


async def grant_user_access(
    db: AsyncSession, desktop_id: UUID, user_id: UUID, role: models.DesktopAccessRole
) -> models.DesktopUserAccess:
    db_access = models.DesktopUserAccess(desktop_id=desktop_id, user_id=user_id, role=role)
    db.add(db_access)
    await db.commit()
    await db.refresh(db_access)

    return db_access


async def get_user_access_by_id(db: AsyncSession, access_id: UUID) -> models.DesktopUserAccess | None:
    stmt = select(models.DesktopUserAccess).where(models.DesktopUserAccess.id == access_id)
    result = await db.execute(stmt)

    return result.scalar()


async def set_user_access(
    db: AsyncSession, desktop_id: UUID, user_id: UUID, role: models.DesktopAccessRole
) -> models.DesktopUserAccess:
    stmt = select(models.DesktopUserAccess).where(
        models.DesktopUserAccess.desktop_id == desktop_id,
        models.DesktopUserAccess.user_id == user_id,
    )
    result = await db.execute(stmt)
    existing = result.scalar()
    if existing:
        existing.role = role
        await db.commit()
        await db.refresh(existing)
        return existing
    return await grant_user_access(db, desktop_id, user_id, role)


async def update_user_access_role(
    db: AsyncSession, db_access: models.DesktopUserAccess, role: models.DesktopAccessRole
) -> models.DesktopUserAccess:
    db_access.role = role
    await db.commit()
    await db.refresh(db_access)

    return db_access


async def revoke_user_access(db: AsyncSession, db_access: models.DesktopUserAccess) -> None:
    await db.delete(db_access)
    await db.commit()


# --- Organization access ---

async def org_access_exists(db: AsyncSession, desktop_id: UUID, organization_id: UUID) -> bool:
    stmt = select(
        exists()
        .where(models.DesktopOrganizationAccess.desktop_id == desktop_id)
        .where(models.DesktopOrganizationAccess.organization_id == organization_id)
    )
    result = await db.execute(stmt)

    return bool(result.scalar())


async def grant_org_access(
    db: AsyncSession, desktop_id: UUID, organization_id: UUID, role: models.DesktopAccessRole
) -> models.DesktopOrganizationAccess:
    db_access = models.DesktopOrganizationAccess(desktop_id=desktop_id, organization_id=organization_id, role=role)
    db.add(db_access)
    await db.commit()
    await db.refresh(db_access)

    return db_access


async def get_org_access_by_id(db: AsyncSession, access_id: UUID) -> models.DesktopOrganizationAccess | None:
    stmt = select(models.DesktopOrganizationAccess).where(models.DesktopOrganizationAccess.id == access_id)
    result = await db.execute(stmt)

    return result.scalar()


async def update_org_access_role(
    db: AsyncSession, db_access: models.DesktopOrganizationAccess, role: models.DesktopAccessRole
) -> models.DesktopOrganizationAccess:
    db_access.role = role
    await db.commit()
    await db.refresh(db_access)

    return db_access


async def revoke_org_access(db: AsyncSession, db_access: models.DesktopOrganizationAccess) -> None:
    await db.delete(db_access)
    await db.commit()


# --- Desktop invites ---

async def create_desktop_invite(
    db: AsyncSession,
    inviter: models.User,
    desktop: models.Desktop,
    role: models.DesktopAccessRole,
    expires_in_hours: int,
    invitee_user: models.User | None = None,
    invitee_organization: models.Organization | None = None,
) -> models.DesktopInvite:
    db_invite = models.DesktopInvite(
        desktop_id=desktop.id,
        inviter_id=inviter.id,
        role=role,
        status=models.InvitationStatus.pending,
        expires_at=helpers.utcnow() + timedelta(hours=expires_in_hours),
        invitee_user_id=invitee_user.id if invitee_user else None,
        invitee_organization_id=invitee_organization.id if invitee_organization else None,
    )

    db.add(db_invite)
    await db.commit()
    await db.refresh(db_invite)

    return db_invite


async def get_desktop_invite_by_id(db: AsyncSession, invite_id: UUID) -> models.DesktopInvite | None:
    stmt = select(models.DesktopInvite).where(models.DesktopInvite.id == invite_id)
    result = await db.execute(stmt)

    return result.scalar()


async def get_pending_user_invite(
    db: AsyncSession, desktop_id: UUID, invitee_user_id: UUID
) -> models.DesktopInvite | None:
    stmt = select(models.DesktopInvite).where(
        models.DesktopInvite.desktop_id == desktop_id,
        models.DesktopInvite.invitee_user_id == invitee_user_id,
        models.DesktopInvite.status == models.InvitationStatus.pending,
        models.DesktopInvite.expires_at > helpers.utcnow(),
    )
    result = await db.execute(stmt)

    return result.scalar()


async def get_pending_org_invite(
    db: AsyncSession, desktop_id: UUID, organization_id: UUID
) -> models.DesktopInvite | None:
    stmt = select(models.DesktopInvite).where(
        models.DesktopInvite.desktop_id == desktop_id,
        models.DesktopInvite.invitee_organization_id == organization_id,
        models.DesktopInvite.status == models.InvitationStatus.pending,
        models.DesktopInvite.expires_at > helpers.utcnow(),
    )
    result = await db.execute(stmt)

    return result.scalar()


async def change_desktop_invite_status(
    db: AsyncSession, invite: models.DesktopInvite, status: models.InvitationStatus
) -> None:
    invite.status = status
    await db.commit()


async def respond_to_desktop_user_invite(
    db: AsyncSession, invite: models.DesktopInvite, status: models.InvitationStatus
) -> models.DesktopUserAccess | None:
    await change_desktop_invite_status(db, invite, status)

    if status == models.InvitationStatus.accepted:
        invite.accepted_at = helpers.utcnow()
        await db.commit()

        return await grant_user_access(db, invite.desktop_id, invite.invitee_user_id, invite.role)

    return None


async def respond_to_desktop_org_invite(
    db: AsyncSession, invite: models.DesktopInvite, status: models.InvitationStatus
) -> models.DesktopOrganizationAccess | None:
    await change_desktop_invite_status(db, invite, status)

    if status == models.InvitationStatus.accepted:
        invite.accepted_at = helpers.utcnow()
        await db.commit()

        return await grant_org_access(db, invite.desktop_id, invite.invitee_organization_id, invite.role)

    return None


async def list_desktop_invites_inbox(db: AsyncSession, user: models.User) -> Sequence[models.DesktopInvite]:
    """Returns pending user invites for the given user plus pending org invites for orgs they own."""
    user_invites_stmt = (
        select(models.DesktopInvite)
        .options(joinedload(models.DesktopInvite.desktop))
        .where(
            models.DesktopInvite.invitee_user_id == user.id,
            models.DesktopInvite.status == models.InvitationStatus.pending,
        )
    )

    owned_org_ids = select(models.Organization.id).where(models.Organization.owner_id == user.id)
    org_invites_stmt = (
        select(models.DesktopInvite)
        .options(joinedload(models.DesktopInvite.desktop))
        .where(
            models.DesktopInvite.invitee_organization_id.in_(owned_org_ids),
            models.DesktopInvite.status == models.InvitationStatus.pending,
        )
    )

    user_result = await db.execute(user_invites_stmt)
    org_result = await db.execute(org_invites_stmt)

    return list(user_result.scalars().unique().all()) + list(org_result.scalars().unique().all())


async def list_desktop_invites_outbox(db: AsyncSession, user: models.User) -> Sequence[models.DesktopInvite]:
    stmt = select(models.DesktopInvite).where(
        models.DesktopInvite.inviter_id == user.id,
        models.DesktopInvite.status == models.InvitationStatus.pending,
    )

    result = await db.execute(stmt)

    return result.scalars().all()


# --- Key aggregation ---

async def get_desktop_access_public_keys(db: AsyncSession, desktop_id: UUID) -> list[dict[str, Any]]:
    direct_users = (
        select(models.DesktopUserAccess.user_id.label("user_id"), models.DesktopUserAccess.role.label("authrole"))
        .where(models.DesktopUserAccess.desktop_id == desktop_id)
        .subquery()
    )

    org_users = (
        select(
            models.OrganizationMember.user_id.label("user_id"),
            models.DesktopOrganizationAccess.role.label("authrole"),
        )
        .join(
            models.DesktopOrganizationAccess,
            models.DesktopOrganizationAccess.organization_id == models.OrganizationMember.organization_id,
        )
        .where(models.DesktopOrganizationAccess.desktop_id == desktop_id)
        .subquery()
    )

    base_users = union_all(select(direct_users), select(org_users)).subquery()

    principal_query = (
        select(models.User.email.label("authid"), models.Principal.public_key.label("public_key"), base_users.c.authrole)
        .join(base_users, models.Principal.user_id == base_users.c.user_id)
        .join(models.User, models.User.id == models.Principal.user_id)
        .where(models.Principal.expires_at > func.now())
    )

    device_query = (
        select(models.User.email.label("authid"), models.Device.public_key.label("public_key"), base_users.c.authrole)
        .join(base_users, models.Device.user_id == base_users.c.user_id)
        .join(models.User, models.User.id == models.Device.user_id)
    )

    desktop_query = select(
        models.Desktop.authid.label("authid"), models.Desktop.public_key.label("public_key"), base_users.c.authrole
    ).join(base_users, models.Desktop.user_id == base_users.c.user_id)

    keys_union = union_all(principal_query, device_query, desktop_query).subquery()

    stmt = select(keys_union.c.authid, keys_union.c.public_key, keys_union.c.authrole).distinct()
    result = await db.execute(stmt)

    desktop_authorizations: dict[str, dict] = {}
    for authid, public_key, authrole in result.all():
        if authid not in desktop_authorizations:
            desktop_authorizations[authid] = {
                "authid": authid,
                "authorized_keys": [],
                "authrole": authrole,
            }
        elif _ROLE_PRIORITY.get(authrole, 0) > _ROLE_PRIORITY.get(desktop_authorizations[authid]["authrole"], 0):
            desktop_authorizations[authid]["authrole"] = authrole

        desktop_authorizations[authid]["authorized_keys"].append(public_key)

    return list(desktop_authorizations.values())


async def has_desktop_access(db: AsyncSession, desktop_id: UUID, user_id: UUID) -> bool:
    direct = select(
        exists()
        .where(models.DesktopUserAccess.desktop_id == desktop_id)
        .where(models.DesktopUserAccess.user_id == user_id)
    )
    result = await db.execute(direct)
    if result.scalar():
        return True

    via_org = select(
        exists(
            select(models.DesktopOrganizationAccess.id)
            .join(
                models.OrganizationMember,
                models.OrganizationMember.organization_id == models.DesktopOrganizationAccess.organization_id,
            )
            .where(models.DesktopOrganizationAccess.desktop_id == desktop_id)
            .where(models.OrganizationMember.user_id == user_id)
        )
    )
    result = await db.execute(via_org)

    return bool(result.scalar())



# --- Cleanup helpers ---

async def delete_user_desktop_access(db: AsyncSession, db_user: models.User) -> None:
    stmt = delete(models.DesktopUserAccess).where(models.DesktopUserAccess.user_id == db_user.id)
    await db.execute(stmt)


async def delete_user_desktops(db: AsyncSession, db_user: models.User) -> None:
    stmt = delete(models.Desktop).where(models.Desktop.user_id == db_user.id)
    await db.execute(stmt)


async def list_user_accesses(db: AsyncSession, desktop_id: UUID) -> Sequence[models.DesktopUserAccess]:
    stmt = (
        select(models.DesktopUserAccess)
        .options(joinedload(models.DesktopUserAccess.user))
        .where(models.DesktopUserAccess.desktop_id == desktop_id)
    )
    result = await db.execute(stmt)
    return result.scalars().unique().all()


async def list_org_accesses(db: AsyncSession, desktop_id: UUID) -> Sequence[models.DesktopOrganizationAccess]:
    stmt = (
        select(models.DesktopOrganizationAccess)
        .options(joinedload(models.DesktopOrganizationAccess.organization))
        .where(models.DesktopOrganizationAccess.desktop_id == desktop_id)
    )
    result = await db.execute(stmt)
    return result.scalars().unique().all()
