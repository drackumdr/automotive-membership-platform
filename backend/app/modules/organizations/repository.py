import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.organizations.models import Branch, Organization


def descendant_ids(db: Session, roots: set[uuid.UUID]) -> set[uuid.UUID]:
    """Organizaciones raíz más todas sus descendientes (árbol pequeño: se recorre en memoria)."""
    children: dict = defaultdict(list)
    for oid, parent in db.execute(select(Organization.id, Organization.parent_id)).all():
        children[parent].append(oid)
    result, stack = set(roots), list(roots)
    while stack:
        for child in children.get(stack.pop(), []):
            if child not in result:
                result.add(child)
                stack.append(child)
    return result


def list_organizations(db: Session, scope: set[uuid.UUID] | None) -> list[Organization]:
    q = select(Organization).order_by(Organization.name)
    if scope is not None:
        q = q.where(Organization.id.in_(scope))
    return list(db.scalars(q))


def list_branches(db: Session, scope: set[uuid.UUID] | None) -> list[Branch]:
    q = select(Branch).order_by(Branch.name)
    if scope is not None:
        q = q.where(Branch.organization_id.in_(scope))
    return list(db.scalars(q))
