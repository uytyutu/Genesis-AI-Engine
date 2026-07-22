"""R3.12.3 — Password Creation domain (primary credentials only)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.portal.account import new_account
from app.portal.activation_token import activate_token, new_activation_token
from app.portal.password_credential import (
    ENGINE_ID,
    PasswordCredentialError,
    complete_account_activation,
    create_primary_password,
    is_ready_for_authentication,
)


def test_engine_id():
    assert ENGINE_ID == "password_credential_domain_v1"


def test_full_sequence_to_ready():
    account = new_account(email="Owner@Ex.DE", display_name="Owner")
    assert account.status == "pending_activation"

    token = activate_token(new_activation_token(account))
    activated, used = complete_account_activation(account, token)
    assert activated.status == "activated"
    assert used.status == "used"
    assert not is_ready_for_authentication(activated)

    ready, cred = create_primary_password(
        activated,
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$opaque",
        activation_token=used,
    )
    assert ready.status == "ready"
    assert is_ready_for_authentication(ready)
    assert cred.account_id == ready.account_id
    assert cred.status == "active"
    assert "password_hash" in cred.as_dict()
    assert "password" not in cred.as_dict()


def test_password_requires_activated_and_used_token():
    account = new_account(email="a@b.c", display_name="A")
    token = activate_token(new_activation_token(account))
    with pytest.raises(PasswordCredentialError, match="activated"):
        create_primary_password(
            account,
            password_hash="x" * 16,
            activation_token=token,
        )

    activated, used = complete_account_activation(account, token)
    with pytest.raises(PasswordCredentialError, match="used"):
        create_primary_password(
            activated,
            password_hash="x" * 16,
            activation_token=token,  # still active — wrong
        )

    ready, cred = create_primary_password(
        activated,
        password_hash="x" * 16,
        activation_token=used,
    )
    with pytest.raises(PasswordCredentialError, match="already set"):
        create_primary_password(
            ready,
            password_hash="y" * 16,
            activation_token=used,
            existing=cred,
        )


def test_activation_token_account_mismatch():
    a = new_account(email="a@b.c", display_name="A")
    b = new_account(email="b@b.c", display_name="B")
    token = activate_token(new_activation_token(b))
    with pytest.raises(PasswordCredentialError, match="mismatch"):
        complete_account_activation(a, token)


def test_empty_hash_rejected():
    account = new_account(email="a@b.c", display_name="A")
    token = activate_token(new_activation_token(account))
    activated, used = complete_account_activation(account, token)
    with pytest.raises(PasswordCredentialError, match="non-empty"):
        create_primary_password(
            activated,
            password_hash="   ",
            activation_token=used,
        )


def test_does_not_authenticate():
    """Password creation yields ready — not a session / login artifact."""
    account = new_account(email="a@b.c", display_name="A")
    token = activate_token(new_activation_token(account))
    activated, used = complete_account_activation(account, token)
    ready, cred = create_primary_password(
        activated,
        password_hash="hash-material-001",
        activation_token=used,
    )
    assert ready.status == "ready"
    assert not hasattr(ready, "session")
    assert not hasattr(cred, "token")
    assert not hasattr(cred, "jwt")


def test_no_auth_imports():
    import app.portal.password_credential as mod

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
