import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core import audit
from app.core.exceptions import Conflict, Forbidden, NotFound, Unauthorized, ValidationFailed
from app.core.permissions import PERMISSIONS, ROLES
from app.core.security import (
    create_access_token,
    dummy_verify,
    hash_password,
    hash_token,
    new_refresh_token,
    password_needs_rehash,
    verify_password,
)
from app.core.time import as_utc, utcnow
from app.modules.identity import repository as repo
from app.modules.identity.models import (
    USER_ACTIVE,
    USER_DISABLED,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
    UserSession,
)
from app.modules.identity.permissions import AuthContext
from app.modules.identity.schemas import RoleAssignmentIn, TokenPair, UserCreate, UserUpdate
from app.modules.organizations.models import Organization

INVALID = "Credenciales inválidas"


# ---------------------------------------------------------------- sesiones
def _issue_tokens(db: Session, user: User, ip: str | None, user_agent: str | None) -> TokenPair:
    settings = get_settings()
    raw, token_hash = new_refresh_token()
    session = UserSession(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=token_hash,
        expires_at=utcnow() + timedelta(days=settings.refresh_token_days),
        ip=ip,
        user_agent=(user_agent or "")[:300] or None,
    )
    db.add(session)
    access, exp = create_access_token(user.id, session.id)
    return TokenPair(access_token=access, refresh_token=raw, expires_in=settings.access_token_minutes * 60)


def login(db: Session, username: str, password: str, ip: str | None, user_agent: str | None) -> TokenPair:
    settings = get_settings()
    now = utcnow()
    username = username.strip().lower()
    user = repo.get_user_by_username(db, username)
    if user is None:
        dummy_verify(password)
        audit.record(db, "login_failed", ip=ip, details={"username": username[:60], "reason": "unknown_user"})
        db.commit()
        raise Unauthorized(INVALID, code="invalid_credentials")
    if user.locked_until and as_utc(user.locked_until) > now:
        audit.record(db, "login_blocked", user_id=user.id, ip=ip, details={"reason": "locked"})
        db.commit()
        raise Unauthorized(INVALID, code="invalid_credentials")
    ok = verify_password(user.password_hash, password)
    if not ok or user.status != USER_ACTIVE:
        if not ok:
            user.failed_login_count += 1
            if user.failed_login_count >= settings.max_failed_logins:
                user.locked_until = now + timedelta(minutes=settings.lockout_minutes)
                user.failed_login_count = 0
        audit.record(db, "login_failed", user_id=user.id, ip=ip, details={"reason": "bad_password" if not ok else "disabled"})
        db.commit()
        raise Unauthorized(INVALID, code="invalid_credentials")
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    tokens = _issue_tokens(db, user, ip, user_agent)
    audit.record(db, "login_success", user_id=user.id, ip=ip)
    db.commit()
    return tokens


def refresh(db: Session, raw_token: str, ip: str | None, user_agent: str | None) -> TokenPair:
    session = repo.get_session_by_hash(db, hash_token(raw_token))
    if session is None:
        raise Unauthorized("Token de renovación inválido")
    if session.revoked_at is not None:
        if session.revoked_reason == "rotated":  # reutilización: posible robo del token
            repo.revoke_user_sessions(db, session.user_id, "refresh_reuse")
            audit.record(db, "refresh_reuse_detected", user_id=session.user_id, ip=ip)
            db.commit()
        raise Unauthorized("Token de renovación inválido")
    user = db.get(User, session.user_id)
    if as_utc(session.expires_at) <= utcnow() or user is None or user.status != USER_ACTIVE:
        raise Unauthorized("Token de renovación inválido")
    session.revoked_at, session.revoked_reason = utcnow(), "rotated"
    tokens = _issue_tokens(db, user, ip, user_agent)
    db.commit()
    return tokens


def logout(db: Session, ctx: AuthContext) -> None:
    session = db.get(UserSession, ctx.session_id)
    if session and session.revoked_at is None:
        session.revoked_at, session.revoked_reason = utcnow(), "logout"
    audit.record(db, "logout", user_id=ctx.user.id, ip=ctx.ip)
    db.commit()


def change_password(db: Session, ctx: AuthContext, current: str, new: str) -> None:
    user = ctx.user
    if not verify_password(user.password_hash, current):
        audit.record(db, "password_change_failed", user_id=user.id, ip=ctx.ip)
        db.commit()
        raise Forbidden("Contraseña actual incorrecta")
    if new == current or new.lower() == user.username:
        raise ValidationFailed("La nueva contraseña no es válida")
    user.password_hash = hash_password(new)
    repo.revoke_user_sessions(db, user.id, "password_changed", except_session=ctx.session_id)
    audit.record(db, "password_changed", user_id=user.id, ip=ctx.ip)
    db.commit()


def request_recovery(db: Session, identifier: str, ip: str | None) -> None:
    """Respuesta siempre igual. El envío del correo se conectará con integrations/email."""
    user = repo.get_user_by_identifier(db, identifier.strip().lower())
    audit.record(db, "password_recovery_requested", user_id=user.id if user else None, ip=ip)
    db.commit()


# ---------------------------------------------------------------- usuarios
def _check_assignment(db: Session, ctx: AuthContext, a: RoleAssignmentIn) -> Role:
    role = repo.get_role_by_name(db, a.role)
    if role is None:
        raise NotFound("Rol no encontrado")
    if a.organization_id is not None and db.get(Organization, a.organization_id) is None:
        raise NotFound("Organización no encontrada")
    if not ctx.can("users.manage", a.organization_id):
        raise NotFound("Organización no encontrada")  # fuera de su alcance: no se revela
    for code in repo.role_permission_codes(db, role.id):
        if not ctx.can(code, a.organization_id):
            raise Forbidden("No puede otorgar permisos que usted no posee en ese alcance")
    return role


def _visible_user(db: Session, ctx: AuthContext, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    scope = ctx.scope("users.manage")
    if user is None:
        raise NotFound("Usuario no encontrado")
    if scope is not None:
        orgs = {o for _, _, o in repo.user_assignments(db, user_id)}
        if not (orgs & scope):
            raise NotFound("Usuario no encontrado")
    return user


def create_user(db: Session, ctx: AuthContext, data: UserCreate) -> User:
    roles = [(_check_assignment(db, ctx, a), a.organization_id) for a in data.roles]
    user = User(name=data.name.strip(), username=data.username, email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise Conflict("El usuario o correo ya existe") from None
    for role, org in roles:
        db.add(UserRole(user_id=user.id, role_id=role.id, organization_id=org))
    audit.record(db, "user_created", user_id=ctx.user.id, entity_type="user", entity_id=user.id, ip=ctx.ip)
    db.commit()
    return user


def list_users(db: Session, ctx: AuthContext, limit: int, offset: int) -> list[User]:
    q = select(User).order_by(User.username).limit(limit).offset(offset)
    scope = ctx.scope("users.manage")
    if scope is not None:
        q = q.where(User.id.in_(select(UserRole.user_id).where(UserRole.organization_id.in_(scope))))
    return list(db.scalars(q))


def get_user(db: Session, ctx: AuthContext, user_id: uuid.UUID) -> User:
    return _visible_user(db, ctx, user_id)


def update_user(db: Session, ctx: AuthContext, user_id: uuid.UUID, data: UserUpdate) -> User:
    user = _visible_user(db, ctx, user_id)
    if data.name is not None:
        user.name = data.name.strip()
    if data.status is not None and data.status != user.status:
        if user.id == ctx.user.id:
            raise Conflict("No puede desactivar su propio usuario")
        user.status = data.status
        if data.status == USER_DISABLED:
            repo.revoke_user_sessions(db, user.id, "user_disabled")
        audit.record(db, f"user_{data.status.lower()}", user_id=ctx.user.id, entity_type="user", entity_id=user.id, ip=ctx.ip)
    db.commit()
    return user


def assign_role(db: Session, ctx: AuthContext, user_id: uuid.UUID, a: RoleAssignmentIn) -> None:
    user = _visible_user(db, ctx, user_id)
    role = _check_assignment(db, ctx, a)
    exists = db.scalar(
        select(UserRole.id).where(
            UserRole.user_id == user.id, UserRole.role_id == role.id, UserRole.organization_id.is_(a.organization_id)
            if a.organization_id is None
            else UserRole.organization_id == a.organization_id,
        )
    )
    if exists:
        raise Conflict("El usuario ya tiene ese rol en esa organización")
    db.add(UserRole(user_id=user.id, role_id=role.id, organization_id=a.organization_id))
    audit.record(db, "role_assigned", user_id=ctx.user.id, entity_type="user", entity_id=user.id,
                 organization_id=a.organization_id, ip=ctx.ip, details={"role": a.role})
    db.commit()


def remove_assignment(db: Session, ctx: AuthContext, user_id: uuid.UUID, assignment_id: uuid.UUID) -> None:
    user = _visible_user(db, ctx, user_id)
    ur = db.get(UserRole, assignment_id)
    if ur is None or ur.user_id != user.id or not ctx.can("users.manage", ur.organization_id):
        raise NotFound("Asignación no encontrada")
    db.delete(ur)
    repo.revoke_user_sessions(db, user.id, "roles_changed")
    audit.record(db, "role_removed", user_id=ctx.user.id, entity_type="user", entity_id=user.id,
                 organization_id=ur.organization_id, ip=ctx.ip)
    db.commit()


# ---------------------------------------------------------------- semillas
def seed_rbac(db: Session) -> None:
    """Idempotente: crea permisos, roles y vínculos faltantes."""
    perms = {p.code: p for p in db.scalars(select(Permission))}
    for code, desc in PERMISSIONS.items():
        if code not in perms:
            perms[code] = Permission(code=code, description=desc)
            db.add(perms[code])
    roles = {r.name: r for r in db.scalars(select(Role))}
    for name, (desc, _) in ROLES.items():
        if name not in roles:
            roles[name] = Role(name=name, description=desc)
            db.add(roles[name])
    db.flush()
    existing = {(rp.role_id, rp.permission_id) for rp in db.scalars(select(RolePermission))}
    for name, (_, codes) in ROLES.items():
        for code in codes:
            key = (roles[name].id, perms[code].id)
            if key not in existing:
                db.add(RolePermission(role_id=key[0], permission_id=key[1]))
    db.commit()


def create_superadmin(db: Session, username: str, name: str, password: str) -> User:
    if len(password) < 10:
        raise ValidationFailed("La contraseña debe tener al menos 10 caracteres")
    seed_rbac(db)
    user = User(name=name.strip(), username=username.strip().lower(), password_hash=hash_password(password))
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise Conflict("El usuario ya existe") from None
    role = repo.get_role_by_name(db, "superadmin")
    db.add(UserRole(user_id=user.id, role_id=role.id, organization_id=None))
    audit.record(db, "superadmin_created", entity_type="user", entity_id=user.id)
    db.commit()
    return user
