import os
import pathlib
import subprocess
import sys

BACKEND = pathlib.Path(__file__).resolve().parents[2]


def test_alembic_upgrade_head(tmp_path):
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{tmp_path / 'm.db'}", "PYTHONPATH": str(BACKEND)}
    r = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND, env=env, capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
