"""Argon2id, JWT de corta duración y tokens de renovación opacos."""
import hashlib
import secrets
import uuid
from datetime import timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import get_settings
from app.core.time import utcnow

JWT_ALGORITHM = "HS256"  # fijo: no configurable para evitar confusión de algoritmos
_hasher = PasswordHasher()  # Argon2id por defecto
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing")


class TokenError(Exception):
    pass


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def dummy_verify(password: str) -> None:
    """Gasta el mismo tiempo que una verificación real (usuario inexistente)."""
    verify_password(_DUMMY_HASH, password)


def create_access_token(user_id: uuid.UUID, session_id: uuid.UUID, expires_delta: timedelta | None = None):
    settings = get_settings()
    now = utcnow()
    exp = now + (expires_delta if expires_delta is not None else timedelta(minutes=settings.access_token_minutes))
    payload = {"sub": str(user_id), "sid": str(session_id), "jti": uuid.uuid4().hex, "iat": now, "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM), exp


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            get_settings().jwt_secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub", "sid"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def new_refresh_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(48)
    return raw, hash_token(raw)
