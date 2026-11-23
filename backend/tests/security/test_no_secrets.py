import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
PATTERN = re.compile(r"(password|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"\s]{6,}['\"]", re.I)
SKIP = {".git", ".venv", "__pycache__", ".dart_tool", "build", ".pytest_cache"}


def test_no_hardcoded_credentials():
    offenders = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or any(part in SKIP for part in p.parts):
            continue
        if p.suffix not in {".py", ".dart", ".yml", ".yaml", ".sh", ".conf", ".service", ".ini"}:
            continue
        if p.name == "test_no_secrets.py":
            continue
        if PATTERN.search(p.read_text(errors="ignore")):
            offenders.append(str(p.relative_to(ROOT)))
    assert not offenders, f"Posibles credenciales en: {offenders}"
