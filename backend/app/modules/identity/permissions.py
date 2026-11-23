"""Contexto de autenticación y RBAC con alcance por organización."""
import uuid
from dataclasses import dataclass, field

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import audit
from app.core.exceptions import Forbidden, Unauthorized
from app.core.security import TokenError, decode_access_token
from app.core.time import as_utc, utcnow
from app.database import get_db
from app.modules.identity import repository as repo
from app.modules.identity.models import USER_ACTIVE, User, UserSession
from app.modules.organizations.repository import descendant_ids

_bearer = HTTPBearer(auto_error=False)
Scope = set[uuid.UUID] | None  # None = alcance global


@dataclass
class Grant:
    role: str
    organization_id: uuid.UUID | None
    permissions: set[str]


@dataclass
class AuthContext:
    db: Session
    user: User
    session_id: uuid.UUID
    ip: str | None
    grants: list[Grant]
    _scopes: dict = field(default_factory=dict)

    def has(self, code: str) -> bool:
        return any(code in g.permissions for g in self.grants)

    def scope(self, code: str) -> Scope:
        """Organizaciones donde el usuario tiene el permiso (incluye descendientes). None = global."""
        if code not in self._scopes:
            roots = [g.organization_id for g in self.grants if code in g.permissions]
            if any(r is None for r in roots):
                self._scopes[code] = None
            else:
                self._scopes[code] = descendant_ids(self.db, set(roots)) if roots else set()
        return self._scopes[code]

    def can(self, code: str, organization_id: uuid.UUID | None) -> bool:
        scope = self.scope(code)
        if organization_id is None:
            return scope is None  # recursos globales exigen permiso global
        return scope is None or organization_id in scope


def get_auth_context(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> AuthContext:
    if creds is None:
        raise Unauthorized("No autenticado")
    try:
        claims = decode_access_token(creds.credentials)
        user_id, session_id = uuid.UUID(claims["sub"]), uuid.UUID(claims["sid"])
    except (TokenError, ValueError):
        raise Unauthorized("Token inválido o expirado") from None
    session = db.get(UserSession, session_id)
    if (
        session is None
        or session.user_id != user_id
        or session.revoked_at is not None
        or as_utc(session.expires_at) <= utcnow()
    ):
        raise Unauthorized("Sesión no válida")
    user = db.get(User, user_id)
    if user is None or user.status != USER_ACTIVE:
        raise Unauthorized("Sesión no válida")
    grants = [Grant(role, org, perms) for (role, org), perms in repo.user_grants(db, user_id).items()]
    ip = request.client.host if request.client else None
    return AuthContext(db=db, user=user, session_id=session_id, ip=ip, grants=grants)


def require_permission(code: str):
    def dependency(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if not ctx.has(code):
            audit.record(ctx.db, "access_denied", user_id=ctx.user.id, ip=ctx.ip, details={"permission": code})
            ctx.db.commit()
            raise Forbidden("Permiso insuficiente")
        return ctx

    return dependency
