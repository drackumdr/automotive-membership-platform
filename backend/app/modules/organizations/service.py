import uuid

from sqlalchemy.orm import Session

from app.core import audit
from app.core.exceptions import Forbidden, NotFound
from app.modules.identity.permissions import AuthContext
from app.modules.organizations import repository as repo
from app.modules.organizations.models import Branch, Organization
from app.modules.organizations.schemas import BranchCreate, BranchUpdate, OrganizationCreate, OrganizationUpdate


def list_organizations(ctx: AuthContext) -> list[Organization]:
    return repo.list_organizations(ctx.db, ctx.scope("organizations.read"))


def get_organization(ctx: AuthContext, org_id: uuid.UUID, permission: str = "organizations.read") -> Organization:
    org = ctx.db.get(Organization, org_id)
    if org is None or not ctx.can(permission, org_id):
        raise NotFound("Organización no encontrada")  # fuera de alcance = no existe
    return org


def create_organization(ctx: AuthContext, data: OrganizationCreate) -> Organization:
    if data.parent_id is None:
        if not ctx.can("organizations.manage", None):
            raise Forbidden("Solo un administrador global puede crear organizaciones raíz")
    else:
        get_organization(ctx, data.parent_id, "organizations.manage")
    org = Organization(name=data.name.strip(), type=data.type, parent_id=data.parent_id)
    ctx.db.add(org)
    ctx.db.flush()
    audit.record(ctx.db, "organization_created", user_id=ctx.user.id, entity_type="organization",
                 entity_id=org.id, organization_id=org.id, ip=ctx.ip)
    ctx.db.commit()
    return org


def update_organization(ctx: AuthContext, org_id: uuid.UUID, data: OrganizationUpdate) -> Organization:
    org = get_organization(ctx, org_id, "organizations.manage")
    if data.name is not None:
        org.name = data.name.strip()
    if data.status is not None:
        org.status = data.status
    audit.record(ctx.db, "organization_updated", user_id=ctx.user.id, entity_type="organization",
                 entity_id=org.id, organization_id=org.id, ip=ctx.ip)
    ctx.db.commit()
    return org


def list_branches(ctx: AuthContext) -> list[Branch]:
    return repo.list_branches(ctx.db, ctx.scope("organizations.read"))


def create_branch(ctx: AuthContext, data: BranchCreate) -> Branch:
    get_organization(ctx, data.organization_id, "organizations.manage")
    branch = Branch(organization_id=data.organization_id, name=data.name.strip(), address=data.address)
    ctx.db.add(branch)
    ctx.db.flush()
    audit.record(ctx.db, "branch_created", user_id=ctx.user.id, entity_type="branch",
                 entity_id=branch.id, organization_id=branch.organization_id, ip=ctx.ip)
    ctx.db.commit()
    return branch


def update_branch(ctx: AuthContext, branch_id: uuid.UUID, data: BranchUpdate) -> Branch:
    branch = ctx.db.get(Branch, branch_id)
    if branch is None or not ctx.can("organizations.manage", branch.organization_id):
        raise NotFound("Sucursal no encontrada")
    if data.name is not None:
        branch.name = data.name.strip()
    if data.address is not None:
        branch.address = data.address
    ctx.db.commit()
    return branch
