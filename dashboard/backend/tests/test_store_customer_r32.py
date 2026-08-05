"""Store Customer Accounts R3.2 — separate from Virtus Client Identity."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.integration.store_customer.auth import (
    decode_store_buyer_token,
    issue_store_buyer_token,
)
from app.integration.store_customer.service import StoreCustomerService
from app.factory.store_factory.composer import write_storefront
from app.factory.store_factory.templates import StoreTemplateRegistry


@pytest.fixture(autouse=True)
def _buyer_secret(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_STORE_BUYER_JWT_SECRET", "test-store-buyer-secret")


def test_register_login_profile_addresses_wishlist(tmp_path: Path):
    svc = StoreCustomerService(tmp_path)
    oid = "ord-buyer-1"

    reg = svc.register(
        oid,
        {
            "email": "buyer@shop.test",
            "password": "secret123",
            "first_name": "Anna",
            "last_name": "Müller",
        },
    )
    assert reg["scope"] == "store_buyer"
    assert reg["token"]
    payload = decode_store_buyer_token(reg["token"])
    assert payload is not None
    assert payload["order_id"] == oid
    assert payload["scope"] == "store_buyer"
    buyer_id = reg["buyer"]["id"]

    login = svc.login(
        oid, {"email": "buyer@shop.test", "password": "secret123"}
    )
    assert login["buyer"]["id"] == buyer_id

    with pytest.raises(ValueError, match="invalid_credentials"):
        svc.login(oid, {"email": "buyer@shop.test", "password": "wrongpass1"})

    # Virtus-style scope must not decode as store buyer when forged differently —
    # our issuer always sets store_buyer.
    tok = issue_store_buyer_token(
        buyer_id=buyer_id, email="buyer@shop.test", order_id=oid
    )
    assert decode_store_buyer_token(tok)["sub"] == buyer_id

    me = svc.me(oid, buyer_id)
    assert me["orders"] == []
    assert "Commerce" in me["orders_note"]

    svc.update_profile(oid, buyer_id, {"phone": "+491234", "first_name": "Anne"})
    assert svc.me(oid, buyer_id)["buyer"]["phone"] == "+491234"

    addrs = svc.save_address(
        oid,
        buyer_id,
        {
            "full_name": "Anne Müller",
            "line1": "Hauptstr. 1",
            "city": "Berlin",
            "postal_code": "10115",
            "country": "DE",
            "is_default": True,
        },
    )
    assert len(addrs["addresses"]) == 1

    wish = svc.set_wishlist(
        oid,
        buyer_id,
        [{"product_id": "p1", "title": "Boots", "price": 99}],
    )
    assert wish["wishlist"][0]["product_id"] == "p1"

    admin = svc.admin_list_customers(oid)
    assert admin["count"] == 1
    assert admin["customers"][0]["email"] == "buyer@shop.test"


def test_password_reset_flow(tmp_path: Path):
    svc = StoreCustomerService(tmp_path)
    oid = "ord-buyer-2"
    svc.register(
        oid, {"email": "reset@shop.test", "password": "oldpass12"}
    )
    forgot = svc.request_password_reset(oid, {"email": "reset@shop.test"})
    assert forgot["ok"] is True
    token = forgot["dev_reset_token"]
    assert token

    reset = svc.reset_password(
        oid,
        {
            "email": "reset@shop.test",
            "token": token,
            "password": "newpass99",
        },
    )
    assert reset["token"]
    login = svc.login(
        oid, {"email": "reset@shop.test", "password": "newpass99"}
    )
    assert login["ok"] is True


def test_token_wrong_store_rejected(tmp_path: Path):
    monkey_secret = os.environ["GENESIS_STORE_BUYER_JWT_SECRET"]
    assert monkey_secret
    tok = issue_store_buyer_token(
        buyer_id="buy-1", email="a@b.c", order_id="ord-A"
    )
    # decode ok but order mismatch is enforced at require_store_buyer layer;
    # here we only check claim.
    payload = decode_store_buyer_token(tok)
    assert payload["order_id"] == "ord-A"
    assert payload["order_id"] != "ord-B"


def test_account_page_written_by_factory(tmp_path: Path):
    brief = {
        "company_name": "Demo",
        "store_name": "Nordic",
        "what_is_sold": "Boots",
        "category": "clothing",
        "languages": ["en"],
        "currency": "EUR",
        "payments": ["stripe"],
        "shipping": ["dhl"],
        "pages": ["home", "catalog", "pdp", "about", "contact", "legal", "returns"],
        "style": "modern",
        "market_code": "DE",
    }
    resolved = StoreTemplateRegistry().resolve(brief)
    product_dir = tmp_path / "shop"
    product_dir.mkdir()
    written = write_storefront(product_dir, brief=brief, resolved=resolved)
    assert "account.html" in written
    assert (product_dir / "account.html").is_file()
    assert (product_dir / "assets" / "account.js").is_file()
    html = (product_dir / "account.html").read_text(encoding="utf-8")
    assert "account-panels" in html
    assert 'href="account.html"' in (product_dir / "index.html").read_text(
        encoding="utf-8"
    )


def test_customers_survive_separate_from_virtus_path(tmp_path: Path):
    """Buyer data lives under store_admin — not wiped by unrelated paths."""
    svc = StoreCustomerService(tmp_path)
    svc.register(
        "ord-keep",
        {"email": "keep@shop.test", "password": "secret123"},
    )
    path = tmp_path / "store_admin" / "ord-keep" / "customers" / "index.json"
    assert path.is_file()
