import uuid

from fastapi import APIRouter, Depends, status

from app.modules.identity.permissions import AuthContext, require_permission
from app.modules.organizations import service
from app.modules.organizations.schemas import (
    BranchCreate,
    BranchOut,
    BranchUpdate,
    OrganizationCreate,
    OrganizationOut,
    OrganizationUpdate,
)

router = APIRouter(tags=["organizations"])
Read = Depends(require_permission("organizations.read"))
Manage = Depends(require_permission("organizations.manage"))


@router.get("/organizations", response_model=list[OrganizationOut])
def list_organizations(ctx: AuthContext = Read):
    return service.list_organizations(ctx)


@router.post("/organizations", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
def create_organization(body: OrganizationCreate, ctx: AuthContext = Manage):
    return service.create_organization(ctx, body)


@router.get("/organizations/{org_id}", response_model=OrganizationOut)
def get_organization(org_id: uuid.UUID, ctx: AuthContext = Read):
    return service.get_organization(ctx, org_id)


@router.patch("/organizations/{org_id}", response_model=OrganizationOut)
def update_organization(org_id: uuid.UUID, body: OrganizationUpdate, ctx: AuthContext = Manage):
    return service.update_organization(ctx, org_id, body)


@router.get("/branches", response_model=list[BranchOut])
def list_branches(ctx: AuthContext = Read):
    return service.list_branches(ctx)


@router.post("/branches", response_model=BranchOut, status_code=status.HTTP_201_CREATED)
def create_branch(body: BranchCreate, ctx: AuthContext = Manage):
    return service.create_branch(ctx, body)


@router.patch("/branches/{branch_id}", response_model=BranchOut)
def update_branch(branch_id: uuid.UUID, body: BranchUpdate, ctx: AuthContext = Manage):
    return service.update_branch(ctx, branch_id, body)
