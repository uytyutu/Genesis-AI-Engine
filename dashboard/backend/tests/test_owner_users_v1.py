"""Owner Users v1 — list/search/card on customer identity SSOT."""

from __future__ import annotations

import json
from pathlib import Path

from app.integration.customer_identity.schema import CustomerCard
from app.integration.customer_identity.store import CustomerIdentityStore
from app.integration.customer_identity.support_center import SupportCenterService


def _seed_user(mem: Path, *, cid: str, email: str, name: str, company: str = "") -> None:
    store = CustomerIdentityStore(mem)
    card = CustomerCard(
        customer_id=cid,
        email=email,
        name=name,
        company_display_name=company,
        phone="+49 30 111",
        account_status="active",
        registered_at="2026-08-01T10:00:00+00:00",
    )
    store.save_card(card)


def test_owner_users_list_and_search(tmp_path: Path):
    _seed_user(
        tmp_path,
        cid="cust-real-1",
        email="owner@handwerk.de",
        name="Hans Müller",
        company="Müller Bau",
    )
    _seed_user(
        tmp_path,
        cid="cust-demo-1",
        email="b3-review-gate@virtuscore-test.example",
        name="B3 Review",
        company="Demo Co",
    )
    (tmp_path / "sales_orders.json").write_text(
        json.dumps(
            [
                {
                    "order_id": "ord-1",
                    "customer_id": "cust-real-1",
                    "email": "owner@handwerk.de",
                    "status": "ready",
                    "package_name": "Website Business",
                    "price_eur": 599,
                    "product_kind": "website",
                    "product_id": "prod-1",
                    "download_ready": True,
                    "created_at": "2026-08-20T12:00:00+00:00",
                    "paid_at": "2026-08-20T12:00:00+00:00",
                }
            ]
        ),
        encoding="utf-8",
    )
    svc = SupportCenterService(tmp_path)

    listed = svc.list_users(limit=50)
    assert listed["ok"] is True
    assert listed["count"] >= 2
    ids = {u["customer_id"] for u in listed["users"]}
    assert "cust-real-1" in ids
    real = next(u for u in listed["users"] if u["customer_id"] == "cust-real-1")
    assert real["products_count"] == 1
    assert real["last_order_id"] == "ord-1"
    assert real["is_demo_test"] is False
    demo = next(u for u in listed["users"] if u["customer_id"] == "cust-demo-1")
    assert demo["is_demo_test"] is True

    by_email = svc.list_users(query="owner@handwerk.de")
    assert by_email["count"] == 1
    assert by_email["users"][0]["customer_id"] == "cust-real-1"

    by_company = svc.list_users(query="Müller Bau")
    assert any(u["customer_id"] == "cust-real-1" for u in by_company["users"])

    by_id = svc.list_users(query="cust-real-1")
    assert by_id["count"] >= 1

    empty = svc.list_users(query="zzz-no-such-user-xyz")
    assert empty["empty"] is True
    assert empty["empty_message_de"] == "Kein Kunde gefunden."

    hidden = svc.list_users(include_demo_test=False)
    assert all(not u["is_demo_test"] for u in hidden["users"])


def test_owner_user_card_chain_and_websites(tmp_path: Path):
    _seed_user(
        tmp_path,
        cid="cust-real-2",
        email="mira@atelier.de",
        name="Mira",
        company="Atelier Mira",
    )
    (tmp_path / "sales_orders.json").write_text(
        json.dumps(
            [
                {
                    "order_id": "ord-web",
                    "customer_id": "cust-real-2",
                    "email": "mira@atelier.de",
                    "status": "ready",
                    "package_name": "Website Basic",
                    "product_kind": "website",
                    "product_id": "web-prod-9",
                    "download_ready": True,
                    "price_eur": 299,
                    "created_at": "2026-08-21T10:00:00+00:00",
                }
            ]
        ),
        encoding="utf-8",
    )
    card = SupportCenterService(tmp_path).build_client_card("cust-real-2")
    assert card is not None
    assert card["customer_id"] == "cust-real-2"
    assert card["module"] == "owner_users_v1"
    assert card["chain"]["user"] == "cust-real-2"
    assert "ord-web" in card["chain"]["orders"]
    assert card["websites"]
    assert card["websites"][0]["preview_href"].endswith("/preview")
    assert card["websites"][0]["download_href"].endswith("/download")
    assert any(a.get("id") == "add_note" for a in card["actions"])


def test_owner_users_empty_registry(tmp_path: Path):
    listed = SupportCenterService(tmp_path).list_users()
    assert listed["empty"] is True
    assert listed["empty_message_de"] == "Noch keine Kunden registriert."
