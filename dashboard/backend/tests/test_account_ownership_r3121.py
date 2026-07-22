"""R3.12.1 — Account Ownership Architecture (domain only)."""

from __future__ import annotations

from app.portal.account import ENGINE_ID as ACCOUNT_ENGINE, Account, new_account
from app.portal.account_ownership_architecture import (
    ENGINE_ID as ARCH_ENGINE,
    OWNERSHIP_FUTURE_ROLES,
)
from app.portal.client import new_client, website_for_client
from app.portal.invitation import ENGINE_ID as INVITE_ENGINE, new_website_invitation
from app.portal.ownership import (
    ENGINE_ID as OWNERSHIP_ENGINE,
    FUTURE_ROLES,
    account_ids_for_website,
    grant_website_ownership,
    ownership_for_account_website,
    website_ids_for_account,
)


def test_engine_ids():
    assert ACCOUNT_ENGINE == "account_domain_v1"
    assert OWNERSHIP_ENGINE == "website_ownership_v1"
    assert INVITE_ENGINE == "website_invitation_v1"
    assert ARCH_ENGINE == "account_ownership_architecture_v1"


def test_account_is_not_client():
    account = new_account(email="Owner@Example.DE", display_name="Anna")
    client = new_client(display_name="Dental GmbH", primary_email="billing@dental.de")
    assert isinstance(account, Account)
    assert account.email == "owner@example.de"
    assert account.status == "pending_activation"
    assert account.account_id != client.client_id
    assert not hasattr(account, "client_id")
    assert not hasattr(client, "account_id")


def test_multi_site_ownership():
    account = new_account(email="a@b.c", display_name="A")
    client = new_client(display_name="Co", primary_email="c@co.de")
    site_a = website_for_client(client, product_id="p1", market_code="DE")
    site_b = website_for_client(client, product_id="p2", market_code="NL")
    own_a = grant_website_ownership(account, site_a)
    own_b = grant_website_ownership(account, site_b)
    ids = website_ids_for_account([own_a, own_b], account.account_id)
    assert set(ids) == {site_a.website_id, site_b.website_id}
    assert own_a.role == "owner"
    assert site_a.client_id == client.client_id
    assert own_a.account_id == account.account_id


def test_multi_user_ready_same_website():
    client = new_client(display_name="Co", primary_email="c@co.de")
    site = website_for_client(client, product_id="p1", market_code="DE")
    owner = new_account(email="owner@co.de", display_name="Owner")
    helper = new_account(email="helper@co.de", display_name="Helper")
    rows = [
        grant_website_ownership(owner, site),
        grant_website_ownership(helper, site),
    ]
    assert set(account_ids_for_website(rows, site.website_id)) == {
        owner.account_id,
        helper.account_id,
    }
    found = ownership_for_account_website(
        rows, account_id=helper.account_id, website_id=site.website_id
    )
    assert found is not None
    assert found.role == "owner"


def test_invitation_architecture_only():
    client = new_client(display_name="Co", primary_email="c@co.de")
    site = website_for_client(client, product_id="p1", market_code="DE")
    invite = new_website_invitation(
        site,
        invited_email="Marketer@Co.DE",
        expires_at="2026-08-01T00:00:00+00:00",
    )
    assert invite.invited_email == "marketer@co.de"
    assert invite.status == "pending"
    assert invite.intended_role == "owner"
    assert invite.website_id == site.website_id
    # No token / delivery fields — architecture only
    assert not hasattr(invite, "token")
    assert not hasattr(invite, "password_hash")


def test_future_roles_documented_not_implemented():
    assert FUTURE_ROLES == ("owner", "manager", "editor", "viewer")
    assert OWNERSHIP_FUTURE_ROLES == FUTURE_ROLES
    # Only owner is grantable today (type + constructor default)
    account = new_account(email="a@b.c", display_name="A")
    client = new_client(display_name="Co", primary_email="c@co.de")
    site = website_for_client(client, product_id="p1", market_code="DE")
    row = grant_website_ownership(account, site)
    assert row.role == "owner"


def test_no_auth_imports_in_ownership_modules():
    """Guard: ownership domain must not import auth / HTTP stacks."""
    import ast
    from pathlib import Path

    import app.portal.account as account_mod
    import app.portal.invitation as invitation_mod
    import app.portal.ownership as ownership_mod

    banned_roots = {
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
    for mod in (account_mod, ownership_mod, invitation_mod):
        tree = ast.parse(Path(mod.__file__).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            else:
                continue
            for name in names:
                assert name not in banned_roots, f"{mod.__name__} imports {name}"
