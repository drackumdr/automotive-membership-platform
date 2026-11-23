import os
import pathlib
import sqlite3
import subprocess
import sys

BACKEND = pathlib.Path(__file__).resolve().parents[2]
EXPECTED = {"organizations", "branches", "users", "roles", "permissions", "role_permissions",
            "user_roles", "user_sessions", "audit_logs"}


def test_alembic_upgrade_head_creates_schema(tmp_path):
    db_file = tmp_path / "m.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_file}", "PYTHONPATH": str(BACKEND)}
    r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    tables = {row[0] for row in sqlite3.connect(db_file).execute("select name from sqlite_master where type='table'")}
    assert EXPECTED <= tables


def test_models_and_migrations_are_in_sync(tmp_path):
    db_file = tmp_path / "s.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_file}", "PYTHONPATH": str(BACKEND)}
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=env, check=True, capture_output=True)
    r = subprocess.run([sys.executable, "-m", "alembic", "check"], cwd=BACKEND, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
