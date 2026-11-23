from app.modules.identity.models import User, UserRole
from app.modules.identity.repository import get_role_by_name
from app.core.security import hash_password
from app.modules.organizations.models import Organization

DEFAULT_PW = "Clave-de-prueba-123"


def make_org(db, name, type_="CORPORATE", parent=None):
    org = Organization(name=name, type=type_, parent_id=parent.id if parent else None)
    db.add(org)
    db.commit()
    return org


def make_user(db, username, role, org=None, password=DEFAULT_PW):
    user = User(name=username.title(), username=username, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=get_role_by_name(db, role).id, organization_id=org.id if org else None))
    db.commit()
    return user


def login(client, username, password=DEFAULT_PW):
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def auth(client, username, password=DEFAULT_PW):
    return {"Authorization": f"Bearer {login(client, username, password)['access_token']}"}
