import uuid

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.permissions import ROLES
from app.database import get_db
from app.modules.identity import repository as repo
from app.modules.identity import service
from app.modules.identity.permissions import AuthContext, get_auth_context, require_permission
from app.modules.identity.schemas import (
    GrantOut,
    LoginRequest,
    MeOut,
    PasswordChange,
    PasswordRecovery,
    RefreshRequest,
    RoleAssignmentIn,
    RoleAssignmentOut,
    RoleOut,
    TokenPair,
    UserCreate,
    UserOut,
    UserUpdate,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(tags=["users"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@auth_router.post("/login", response_model=TokenPair)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    return service.login(db, body.username, body.password, _ip(request), request.headers.get("user-agent"))


@auth_router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    return service.refresh(db, body.refresh_token, _ip(request), request.headers.get("user-agent"))


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(ctx: AuthContext = Depends(get_auth_context)):
    service.logout(ctx.db, ctx)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_router.post("/password/change", status_code=status.HTTP_204_NO_CONTENT)
def password_change(body: PasswordChange, ctx: AuthContext = Depends(get_auth_context)):
    service.change_password(ctx.db, ctx, body.current_password, body.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_router.post("/password/recovery", status_code=status.HTTP_202_ACCEPTED)
def password_recovery(body: PasswordRecovery, request: Request, db: Session = Depends(get_db)):
    service.request_recovery(db, body.identifier, _ip(request))
    return {"detail": "Si la cuenta existe, recibirá instrucciones."}


@auth_router.get("/me", response_model=MeOut)
def me(ctx: AuthContext = Depends(get_auth_context)):
    grants = [GrantOut(role=g.role, organization_id=g.organization_id, permissions=sorted(g.permissions)) for g in ctx.grants]
    return MeOut(id=ctx.user.id, name=ctx.user.name, username=ctx.user.username, grants=grants)


def _user_out(ctx: AuthContext, user) -> UserOut:
    roles = [RoleAssignmentOut(id=i, role=r, organization_id=o) for i, r, o in repo.user_assignments(ctx.db, user.id)]
    return UserOut(id=user.id, name=user.name, username=user.username, email=user.email, status=user.status, roles=roles)


@users_router.get("/roles", response_model=list[RoleOut])
def list_roles(ctx: AuthContext = Depends(require_permission("users.manage"))):
    return [RoleOut(name=n, description=d, permissions=sorted(p)) for n, (d, p) in ROLES.items()]


@users_router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, ctx: AuthContext = Depends(require_permission("users.manage"))):
    return _user_out(ctx, service.create_user(ctx.db, ctx, body))


@users_router.get("/users", response_model=list[UserOut])
def list_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ctx: AuthContext = Depends(require_permission("users.manage")),
):
    return [_user_out(ctx, u) for u in service.list_users(ctx.db, ctx, limit, offset)]


@users_router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: uuid.UUID, ctx: AuthContext = Depends(require_permission("users.manage"))):
    return _user_out(ctx, service.get_user(ctx.db, ctx, user_id))


@users_router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: uuid.UUID, body: UserUpdate, ctx: AuthContext = Depends(require_permission("users.manage"))):
    return _user_out(ctx, service.update_user(ctx.db, ctx, user_id, body))


@users_router.post("/users/{user_id}/roles", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def assign_role(user_id: uuid.UUID, body: RoleAssignmentIn, ctx: AuthContext = Depends(require_permission("users.manage"))):
    service.assign_role(ctx.db, ctx, user_id, body)
    return _user_out(ctx, service.get_user(ctx.db, ctx, user_id))


@users_router.delete("/users/{user_id}/roles/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_role(user_id: uuid.UUID, assignment_id: uuid.UUID, ctx: AuthContext = Depends(require_permission("users.manage"))):
    service.remove_assignment(ctx.db, ctx, user_id, assignment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
