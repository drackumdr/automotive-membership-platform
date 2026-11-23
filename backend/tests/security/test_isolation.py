import pytest

from tests.helpers import auth, make_org, make_user

API = "/api/v1"


@pytest.fixture
def world(db):
    corp = make_org(db, "Corporativo", "CORPORATE")
    own = make_org(db, "Taller propio", "OWNED_WORKSHOP", corp)
    aff_a = make_org(db, "Afiliado A", "AFFILIATE_WORKSHOP", corp)
    aff_b = make_org(db, "Afiliado B", "AFFILIATE_WORKSHOP", corp)
    other_root = make_org(db, "Otra red", "FRANCHISE")
    make_user(db, "root", "superadmin")
    make_user(db, "boss", "corporate", corp)
    make_user(db, "mec_a", "workshop", aff_a)
    make_user(db, "mec_b", "workshop", aff_b)
    make_user(db, "outsider", "corporate", other_root)
    return dict(corp=corp, own=own, a=aff_a, b=aff_b, other=other_root)


def ids(r):
    return {o["id"] for o in r.json()}


def test_workshop_cannot_reach_other_workshop_by_changing_ids(client, world):
    h = auth(client, "mec_a")
    assert ids(client.get(f"{API}/organizations", headers=h)) == {str(world["a"].id)}
    assert client.get(f"{API}/organizations/{world['a'].id}", headers=h).status_code == 200
    for target in (world["b"], world["corp"], world["other"]):
        assert client.get(f"{API}/organizations/{target.id}", headers=h).status_code == 404


def test_workshop_cannot_modify_or_create_in_other_org(client, world):
    h = auth(client, "mec_a")
    assert client.patch(f"{API}/organizations/{world['b'].id}", headers=h, json={"name": "x"}).status_code in (403, 404)
    assert client.post(f"{API}/branches", headers=h, json={"organization_id": str(world["b"].id), "name": "Sucursal"}).status_code in (403, 404)
    assert client.post(f"{API}/users", headers=h, json={"name": "X", "username": "xx1", "password": "Clave-larga-123",
                       "roles": [{"role": "workshop", "organization_id": str(world["b"].id)}]}).status_code == 403


def test_corporate_sees_descendants_but_not_other_networks(client, world):
    h = auth(client, "boss")
    seen = ids(client.get(f"{API}/organizations", headers=h))
    assert seen == {str(world[k].id) for k in ("corp", "own", "a", "b")}
    assert client.get(f"{API}/organizations/{world['other'].id}", headers=h).status_code == 404
    users = {u["username"] for u in client.get(f"{API}/users", headers=h).json()}
    assert users == {"boss", "mec_a", "mec_b"}  # sin root ni outsider


def test_superadmin_sees_everything(client, world):
    h = auth(client, "root")
    assert len(client.get(f"{API}/organizations", headers=h).json()) == 5
    assert len(client.get(f"{API}/users", headers=h).json()) == 5


def test_no_privilege_escalation(client, world, db):
    h = auth(client, "boss")
    body = lambda role, org: {"name": "N", "username": "nuevo1", "password": "Clave-larga-123", "roles": [{"role": role, "organization_id": org}]}
    # no puede crear superadmin ni roles globales
    assert client.post(f"{API}/users", headers=h, json=body("superadmin", str(world["corp"].id))).status_code == 403
    assert client.post(f"{API}/users", headers=h, json=body("corporate", None)).status_code == 404
    # no puede dar permisos que no tiene (finanzas)
    assert client.post(f"{API}/users", headers=h, json=body("finance", str(world["a"].id))).status_code == 403
    # sí puede crear un mecánico en un taller de su red
    assert client.post(f"{API}/users", headers=h, json=body("workshop", str(world["a"].id))).status_code == 201


def test_corporate_cannot_touch_users_of_other_network(client, world, db):
    from app.modules.identity.repository import get_user_by_username
    outsider = get_user_by_username(db, "outsider")
    h = auth(client, "boss")
    assert client.get(f"{API}/users/{outsider.id}", headers=h).status_code == 404
    assert client.patch(f"{API}/users/{outsider.id}", headers=h, json={"status": "DISABLED"}).status_code == 404


def test_missing_permission_is_403_and_audited(client, world, db):
    from sqlalchemy import select
    from app.modules.identity.models import AuditLog
    h = auth(client, "mec_a")
    assert client.get(f"{API}/users", headers=h).status_code == 403
    assert client.get(f"{API}/roles", headers=h).status_code == 403
    assert "access_denied" in [a for (a,) in db.execute(select(AuditLog.action)).all()]


@pytest.mark.parametrize("method,path", [
    ("get", "/organizations"), ("post", "/organizations"), ("get", "/branches"),
    ("get", "/users"), ("post", "/users"), ("get", "/roles"), ("post", "/auth/logout"),
])
def test_protected_endpoints_require_token(client, method, path):
    assert getattr(client, method)(f"{API}{path}").status_code == 401


def test_only_global_admin_creates_root_organizations(client, world):
    payload = {"name": "Nueva raíz", "type": "FRANCHISE"}
    assert client.post(f"{API}/organizations", headers=auth(client, "boss"), json=payload).status_code == 403
    assert client.post(f"{API}/organizations", headers=auth(client, "root"), json=payload).status_code == 201


def test_corporate_creates_affiliate_and_branch_in_own_tree(client, world):
    h = auth(client, "boss")
    r = client.post(f"{API}/organizations", headers=h, json={"name": "Afiliado C", "type": "AFFILIATE_WORKSHOP", "parent_id": str(world["corp"].id)})
    assert r.status_code == 201
    assert client.post(f"{API}/branches", headers=h, json={"organization_id": r.json()["id"], "name": "Centro"}).status_code == 201
    assert client.post(f"{API}/organizations", headers=h, json={"name": "Intruso", "type": "AFFILIATE_WORKSHOP", "parent_id": str(world["other"].id)}).status_code == 404
