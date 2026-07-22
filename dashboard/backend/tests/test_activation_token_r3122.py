"""R3.12.2 — Activation Token domain (lifecycle only)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.portal.account import new_account
from app.portal.activation_token import (
    ENGINE_ID,
    ActivationTokenError,
    activate_token,
    consume_token,
    expire_token,
    is_usable,
    new_activation_token,
    refresh_expiry_status,
    revoke_token,
)


def test_engine_id():
    assert ENGINE_ID == "activation_token_domain_v1"


def test_create_bound_to_account():
    account = new_account(email="a@b.c", display_name="A")
    token = new_activation_token(account)
    assert token.account_id == account.account_id
    assert token.status == "created"
    assert token.used_at is None
    assert token.revoked_at is None
    assert not is_usable(token)


def test_lifecycle_created_active_used():
    account = new_account(email="a@b.c", display_name="A")
    token = new_activation_token(account)
    active = activate_token(token)
    assert active.status == "active"
    assert is_usable(active)
    used = consume_token(active)
    assert used.status == "used"
    assert used.used_at is not None
    assert not is_usable(used)
    with pytest.raises(ActivationTokenError, match="already used"):
        consume_token(used)


def test_one_shot_from_active_only():
    account = new_account(email="a@b.c", display_name="A")
    created = new_activation_token(account)
    with pytest.raises(ActivationTokenError, match="active"):
        consume_token(created)


def test_expire_and_revoke():
    account = new_account(email="a@b.c", display_name="A")
    created = new_activation_token(account)
    expired = expire_token(created)
    assert expired.status == "expired"
    with pytest.raises(ActivationTokenError):
        activate_token(expired)

    other = activate_token(new_activation_token(account))
    revoked = revoke_token(other)
    assert revoked.status == "revoked"
    assert revoked.revoked_at is not None
    with pytest.raises(ActivationTokenError, match="revoked"):
        consume_token(revoked)


def test_expiry_invariant():
    account = new_account(email="a@b.c", display_name="A")
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    with pytest.raises(ActivationTokenError, match="future"):
        new_activation_token(account, expires_at=past)

    token = new_activation_token(account, ttl=timedelta(hours=1))
    active = activate_token(token)
    after = _parse_future(token.expires_at) + timedelta(seconds=1)
    with pytest.raises(ActivationTokenError, match="expired"):
        consume_token(active, now=after)
    refreshed = refresh_expiry_status(active, now=after)
    assert refreshed.status == "expired"
    assert not is_usable(active, now=after)


def test_terminal_cannot_transition():
    account = new_account(email="a@b.c", display_name="A")
    used = consume_token(activate_token(new_activation_token(account)))
    with pytest.raises(ActivationTokenError):
        revoke_token(used)
    with pytest.raises(ActivationTokenError):
        expire_token(used)


def test_no_auth_imports():
    import ast
    from pathlib import Path

    import app.portal.activation_token as mod

    banned = {
        "jwt",
        "jose",
        "oauth",
        "fastapi",
        "starlette",
        "bcrypt",
        "passlib",
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


def _parse_future(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))
