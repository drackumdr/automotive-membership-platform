from sqlalchemy import select

from app.modules.identity.models import AuditLog
from tests.helpers import DEFAULT_PW, auth, login, make_org, make_user

API = "/api/v1"


def _actions(db):
    return [a for (a,) in db.execute(select(AuditLog.action)).all()]


def test_login_and_me(client, db):
    org = make_org(db, "Corporativo")
    make_user(db, "ana", "corporate", org)
    tokens = login(client, "ANA ")  # normaliza mayúsculas y espacios
    assert tokens["token_type"] == "bearer" and tokens["expires_in"] == 15 * 60
    me = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}).json()
    assert me["username"] == "ana"
    assert me["grants"][0]["role"] == "corporate" and me["grants"][0]["organization_id"] == str(org.id)
    assert "users.manage" in me["grants"][0]["permissions"]
    assert "login_success" in _actions(db)


def test_bad_credentials_are_indistinguishable(client, db):
    make_user(db, "ana", "customer")
    a = client.post(f"{API}/auth/login", json={"username": "ana", "password": "mala-clave-123"})
    b = client.post(f"{API}/auth/login", json={"username": "nadie", "password": "mala-clave-123"})
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()
    assert _actions(db).count("login_failed") == 2


def test_lockout_after_repeated_failures(client, db):
    make_user(db, "ana", "customer")
    for _ in range(5):
        client.post(f"{API}/auth/login", json={"username": "ana", "password": "mala-clave-123"})
    r = client.post(f"{API}/auth/login", json={"username": "ana", "password": DEFAULT_PW})
    assert r.status_code == 401  # bloqueada aun con la clave correcta
    assert "login_blocked" in _actions(db)


def test_requests_without_valid_token_are_401(client):
    assert client.get(f"{API}/auth/me").status_code == 401
    assert client.get(f"{API}/auth/me", headers={"Authorization": "Bearer basura"}).status_code == 401


def test_refresh_rotates_and_detects_reuse(client, db):
    make_user(db, "ana", "customer")
    t1 = login(client, "ana")
    t2 = client.post(f"{API}/auth/refresh", json={"refresh_token": t1["refresh_token"]}).json()
    assert t2["refresh_token"] != t1["refresh_token"]
    # reutilizar el token viejo: se rechaza y se revocan todas las sesiones
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": t1["refresh_token"]}).status_code == 401
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": t2["refresh_token"]}).status_code == 401
    assert client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {t2['access_token']}"}).status_code == 401
    assert "refresh_reuse_detected" in _actions(db)


def test_logout_invalidates_access_token(client, db):
    make_user(db, "ana", "customer")
    t = login(client, "ana")
    h = {"Authorization": f"Bearer {t['access_token']}"}
    assert client.post(f"{API}/auth/logout", headers=h).status_code == 204
    assert client.get(f"{API}/auth/me", headers=h).status_code == 401
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": t["refresh_token"]}).status_code == 401


def test_password_change_revokes_other_sessions(client, db):
    make_user(db, "ana", "customer")
    t_other = login(client, "ana")
    h = auth(client, "ana")
    new = "Nueva-clave-segura-9"
    assert client.post(f"{API}/auth/password/change", headers=h, json={"current_password": "equivocada-123", "new_password": new}).status_code == 403
    assert client.post(f"{API}/auth/password/change", headers=h, json={"current_password": DEFAULT_PW, "new_password": new}).status_code == 204
    assert client.get(f"{API}/auth/me", headers=h).status_code == 200  # la sesión actual sigue
    assert client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {t_other['access_token']}"}).status_code == 401
    assert client.post(f"{API}/auth/login", json={"username": "ana", "password": DEFAULT_PW}).status_code == 401
    assert client.post(f"{API}/auth/login", json={"username": "ana", "password": new}).status_code == 200


def test_short_password_rejected(client, db):
    make_user(db, "ana", "customer")
    h = auth(client, "ana")
    r = client.post(f"{API}/auth/password/change", headers=h, json={"current_password": DEFAULT_PW, "new_password": "corta"})
    assert r.status_code == 422


def test_disabled_user_loses_access(client, db):
    org = make_org(db, "Corporativo")
    make_user(db, "boss", "corporate", org)
    victim = make_user(db, "ana", "customer", org)
    t = login(client, "ana")
    hb = auth(client, "boss")
    assert client.patch(f"{API}/users/{victim.id}", headers=hb, json={"status": "DISABLED"}).status_code == 200
    assert client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {t['access_token']}"}).status_code == 401
    assert client.post(f"{API}/auth/login", json={"username": "ana", "password": DEFAULT_PW}).status_code == 401


def test_password_recovery_does_not_reveal_accounts(client, db):
    make_user(db, "ana", "customer")
    a = client.post(f"{API}/auth/password/recovery", json={"identifier": "ana"})
    b = client.post(f"{API}/auth/password/recovery", json={"identifier": "nadie"})
    assert a.status_code == b.status_code == 202 and a.json() == b.json()
