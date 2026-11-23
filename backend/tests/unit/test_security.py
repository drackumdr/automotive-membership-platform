from datetime import timedelta
import uuid

import jwt
import pytest

from app.core.security import (
    TokenError, create_access_token, decode_access_token, hash_password, hash_token, new_refresh_token, verify_password,
)

PW = "Otra-clave-segura-1"


def test_password_uses_argon2id_and_verifies():
    h = hash_password(PW)
    assert h.startswith("$argon2id$")
    assert verify_password(h, PW)
    assert not verify_password(h, "incorrecta")
    assert not verify_password("no-es-un-hash", PW)


def test_jwt_roundtrip():
    uid, sid = uuid.uuid4(), uuid.uuid4()
    token, _ = create_access_token(uid, sid)
    claims = decode_access_token(token)
    assert claims["sub"] == str(uid) and claims["sid"] == str(sid)


def test_expired_token_rejected():
    token, _ = create_access_token(uuid.uuid4(), uuid.uuid4(), expires_delta=timedelta(seconds=-5))
    with pytest.raises(TokenError):
        decode_access_token(token)


def test_tampered_or_foreign_token_rejected():
    token, _ = create_access_token(uuid.uuid4(), uuid.uuid4())
    with pytest.raises(TokenError):
        decode_access_token(token[:-3] + "abc")
    forged = jwt.encode({"sub": str(uuid.uuid4()), "sid": str(uuid.uuid4()), "exp": 9999999999}, "otro-secreto-" + "z" * 30, algorithm="HS256")
    with pytest.raises(TokenError):
        decode_access_token(forged)


def test_alg_none_rejected():
    unsigned = jwt.encode({"sub": str(uuid.uuid4()), "sid": str(uuid.uuid4()), "exp": 9999999999}, None, algorithm="none")
    with pytest.raises(TokenError):
        decode_access_token(unsigned)


def test_refresh_token_only_hash_is_stored():
    raw, h = new_refresh_token()
    assert h == hash_token(raw) and raw != h and len(raw) >= 48
