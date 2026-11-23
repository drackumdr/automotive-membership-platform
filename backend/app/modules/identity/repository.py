import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.modules.identity.models import Permission, Role, RolePermission, User, UserRole, UserSession


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def get_user_by_identifier(db: Session, identifier: str) -> User | None:
    return db.scalar(select(User).where((User.username == identifier) | (User.email == identifier)))


def get_session_by_hash(db: Session, token_hash: str) -> UserSession | None:
    return db.scalar(select(UserSession).where(UserSession.token_hash == token_hash))


def revoke_user_sessions(db: Session, user_id: uuid.UUID, reason: str, except_session: uuid.UUID | None = None) -> None:
    q = update(UserSession).where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
    if except_session is not None:
        q = q.where(UserSession.id != except_session)
    db.execute(q.values(revoked_at=utcnow(), revoked_reason=reason))


def get_role_by_name(db: Session, name: str) -> Role | None:
    return db.scalar(select(Role).where(Role.name == name))


def role_permission_codes(db: Session, role_id: uuid.UUID) -> set[str]:
    rows = db.scalars(
        select(Permission.code).join(RolePermission, RolePermission.permission_id == Permission.id).where(
            RolePermission.role_id == role_id
        )
    )
    return set(rows)


def user_assignments(db: Session, user_id: uuid.UUID) -> list[tuple[uuid.UUID, str, uuid.UUID | None]]:
    rows = db.execute(
        select(UserRole.id, Role.name, UserRole.organization_id)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user_id)
        .order_by(Role.name)
    ).all()
    return [(r[0], r[1], r[2]) for r in rows]


def user_grants(db: Session, user_id: uuid.UUID) -> dict[tuple[str, uuid.UUID | None], set[str]]:
    rows = db.execute(
        select(Role.name, UserRole.organization_id, Permission.code)
        .select_from(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .join(RolePermission, RolePermission.role_id == Role.id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(UserRole.user_id == user_id)
    ).all()
    grants: dict = {}
    for role, org, code in rows:
        grants.setdefault((role, org), set()).add(code)
    return grants
