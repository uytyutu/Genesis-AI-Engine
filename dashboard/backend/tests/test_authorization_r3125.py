"""R3.12.5 — Authorization Domain (Ownership gate only)."""

from __future__ import annotations

import ast
from pathlib import Path

from app.portal.account import new_account
from app.portal.authorization import (
    DEFAULT_ALLOWED_ROLES,
    ENGINE_ID,
    authorize,
    authorize_account_for_website,
    new_authorization_request,
)
from app.portal.client import new_client, website_for_client
from app.portal.ownership import FUTURE_ROLES, grant_website_ownership


def test_engine_id():
    assert ENGINE_ID == "authorization_domain_v1"
    assert DEFAULT_ALLOWED_ROLES == frozenset({"owner"})
    assert FUTURE_ROLES[0] == "owner"


def test_allowed_via_ownership():
    account = new_account(email="a@b.c", display_name="A", status="ready")
    client = new_client(display_name="Co", primary_email="c@co.de")
    site = website_for_client(client, product_id="p1", market_code="DE")
    ownership = grant_website_ownership(account, site)
    result = authorize_account_for_website(account, site, [ownership])
    assert result.is_allowed
    assert result.outcome == "allowed"
    assert result.matched_role == "owner"
    assert result.ownership_id == ownership.ownership_id
    assert result.denial_reason is None
    assert "session" not in result.as_dict()
    assert "jwt" not in result.as_dict()


def test_denied_without_ownership():
    account = new_account(email="a@b.c", display_name="A", status="ready")
    client = new_client(display_name="Co", primary_email="c@co.de")
    site = website_for_client(client, product_id="p1", market_code="DE")
    result = authorize_account_for_website(account, site, [])
    assert not result.is_allowed
    assert result.denial_reason == "ownership_missing"


def test_no_bypass_account_to_website():
    """Commercial Client link is irrelevant — Ownership is required."""
    account = new_account(email="a@b.c", display_name="A", status="ready")
    client = new_client(display_name="Co", primary_email="c@co.de")
    site = website_for_client(client, product_id="p1", market_code="DE")
    # site.client_id exists but no WebsiteOwnership → denied
    assert site.client_id == client.client_id
    result = authorize_account_for_website(account, site, ownerships=[])
    assert result.denial_reason == "ownership_missing"


def test_role_not_in_allowed_set():
    account = new_account(email="a@b.c", display_name="A", status="ready")
    client = new_client(display_name="Co", primary_email="c@co.de")
    site = website_for_client(client, product_id="p1", market_code="DE")
    ownership = grant_website_ownership(account, site)  # role=owner
    # Future-shaped call: only manager allowed → owner denied
    result = authorize_account_for_website(
        account, site, [ownership], allowed_roles={"manager"}
    )
    assert result.denial_reason == "role_not_allowed"


def test_allowed_roles_set_extensible():
    account = new_account(email="a@b.c", display_name="A", status="ready")
    client = new_client(display_name="Co", primary_email="c@co.de")
    site = website_for_client(client, product_id="p1", market_code="DE")
    ownership = grant_website_ownership(account, site)
    result = authorize_account_for_website(
        account,
        site,
        [ownership],
        allowed_roles={"owner", "manager", "editor", "viewer"},
    )
    assert result.is_allowed
    assert result.matched_role == "owner"


def test_request_result_shape():
    account = new_account(email="a@b.c", display_name="A", status="ready")
    client = new_client(display_name="Co", primary_email="c@co.de")
    site = website_for_client(client, product_id="p1", market_code="DE")
    ownership = grant_website_ownership(account, site)
    request = new_authorization_request(account, site)
    result = authorize(request, [ownership], account=account, website=site)
    assert result.request_id == request.request_id
    assert request.allowed_roles == DEFAULT_ALLOWED_ROLES


def test_does_not_authenticate():
    import app.portal.authorization as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "authenticate(" not in src
    assert "PasswordCredential" not in src


def test_no_web_imports():
    import app.portal.authorization as mod

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
