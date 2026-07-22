"""R3.12.4 — Authentication Domain (credentials check only)."""

from __future__ import annotations

import ast
from pathlib import Path

from app.portal.account import new_account
from app.portal.activation_token import activate_token, new_activation_token
from app.portal.authentication import (
    ENGINE_ID,
    authenticate,
)
from app.portal.password_credential import (
    complete_account_activation,
    create_primary_password,
)


def _ready_account_with_cred(hash_value: str = "stored-hash-abc"):
    account = new_account(email="a@b.c", display_name="A")
    token = activate_token(new_activation_token(account))
    activated, used = complete_account_activation(account, token)
    ready, cred = create_primary_password(
        activated,
        password_hash=hash_value,
        activation_token=used,
    )
    return ready, cred


def test_engine_id():
    assert ENGINE_ID == "authentication_domain_v1"


def test_authenticate_success():
    account, cred = _ready_account_with_cred("same-hash")
    attempt, result = authenticate(
        account, cred, presented_password_hash="same-hash"
    )
    assert attempt.account_id == account.account_id
    assert result.attempt_id == attempt.attempt_id
    assert result.outcome == "authenticated"
    assert result.failure_reason is None
    assert result.is_authenticated
    assert account.status == "ready"  # unchanged
    assert not hasattr(result, "session")
    assert not hasattr(result, "jwt")
    assert "token" not in result.as_dict()


def test_authenticate_hash_mismatch():
    account, cred = _ready_account_with_cred("stored")
    _, result = authenticate(account, cred, presented_password_hash="wrong")
    assert result.outcome == "failed"
    assert result.failure_reason == "hash_mismatch"
    assert not result.is_authenticated


def test_authenticate_requires_ready():
    account = new_account(email="a@b.c", display_name="A")
    _, result = authenticate(account, None, presented_password_hash="x")
    assert result.failure_reason == "account_not_ready"

    token = activate_token(new_activation_token(account))
    activated, used = complete_account_activation(account, token)
    _, result2 = authenticate(activated, None, presented_password_hash="x")
    assert result2.failure_reason == "account_not_ready"


def test_authenticate_missing_credential():
    account, _ = _ready_account_with_cred()
    _, result = authenticate(account, None, presented_password_hash="stored-hash-abc")
    assert result.failure_reason == "credential_missing"


def test_authenticate_suspended():
    account, cred = _ready_account_with_cred("h")
    from dataclasses import replace

    suspended = replace(account, status="suspended")
    _, result = authenticate(suspended, cred, presented_password_hash="h")
    assert result.failure_reason == "account_suspended"


def test_authenticate_account_mismatch():
    account, cred = _ready_account_with_cred("h")
    other = new_account(email="o@b.c", display_name="O", status="ready")
    _, result = authenticate(other, cred, presented_password_hash="h")
    assert result.failure_reason == "account_mismatch"


def test_empty_presented_hash():
    account, cred = _ready_account_with_cred("h")
    _, result = authenticate(account, cred, presented_password_hash="  ")
    assert result.failure_reason == "empty_presented_hash"


def test_no_web_auth_imports():
    import app.portal.authentication as mod

    banned = {
        "jwt",
        "jose",
        "oauth",
        "fastapi",
        "starlette",
        "bcrypt",
        "passlib",
        "argon2",
        "smtp",
        "smtplib",
    }
    tree = ast.parse(Path(mod.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".")[0]]
        else:
            continue
        for name in names:
            assert name not in banned
