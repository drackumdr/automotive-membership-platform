from app.database import get_db
from app.main import app


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_health_database_down(client):
    class BrokenSession:
        def execute(self, *a, **k):
            raise RuntimeError("db caída")

        def close(self):
            pass

    def broken():
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken
    r = client.get("/health")
    assert r.status_code == 503
    assert r.json()["database"] == "error"
