from sqlalchemy import func, select

from app.cli import main
from app.core.permissions import PERMISSIONS, ROLES
from app.modules.identity.models import Permission, Role, RolePermission, User
from app.modules.identity.service import seed_rbac
from app.database import get_sessionmaker
from tests.helpers import auth


def test_seed_is_idempotent_and_complete(db):
    seed_rbac(db)
    seed_rbac(db)
    assert db.scalar(select(func.count()).select_from(Permission)) == len(PERMISSIONS)
    assert db.scalar(select(func.count()).select_from(Role)) == len(ROLES)
    assert db.scalar(select(func.count()).select_from(RolePermission)) == sum(len(c) for _, c in ROLES.values())


def test_role_definitions_only_use_known_permissions():
    for name, (_, codes) in ROLES.items():
        assert set(codes) <= set(PERMISSIONS), name


def test_finance_cannot_approve_repairs_and_workshop_cannot_settle():
    assert "authorizations.approve_basic" not in ROLES["finance"][1]
    assert "finance.settle" not in ROLES["workshop"][1]
    assert "finance.settle" not in ROLES["corporate"][1]


def test_create_superadmin_cli(db, client, monkeypatch):
    monkeypatch.setenv("MEMBERSHIP_ADMIN_PASSWORD", "Admin-inicial-segura-1")
    get_sessionmaker.cache_clear()
    from app import database
    monkeypatch.setattr(database, "get_sessionmaker", lambda: (lambda: db))
    import app.cli as cli
    monkeypatch.setattr(cli, "get_sessionmaker", database.get_sessionmaker)
    assert main(["create-superadmin", "--username", "Admin", "--name", "Administrador"]) == 0
    assert db.scalar(select(User).where(User.username == "admin")) is not None
    h = auth(client, "admin", "Admin-inicial-segura-1")
    assert client.get("/api/v1/auth/me", headers=h).json()["grants"][0]["role"] == "superadmin"
