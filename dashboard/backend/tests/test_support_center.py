"""Business ID + Support Center Client Card (Gen1 support tool)."""

from __future__ import annotations

from pathlib import Path

from app.integration.customer_identity.business_id import (
    generate_business_id,
    normalize_business_id,
)
from app.integration.customer_identity.provision import CustomerProvisioner
from app.integration.customer_identity.support_center import SupportCenterService
from app.integration.launch_readiness import build_launch_readiness


def test_business_id_format():
    bid = generate_business_id()
    assert bid.startswith("VC-")
    assert len(bid) == 12  # VC-XXXX-XXXX
    assert normalize_business_id("vc8q4ml72p") == "VC-8Q4M-L72P"


def test_provision_assigns_business_id(tmp_path: Path):
    prov = CustomerProvisioner(tmp_path)
    account, card, company, welcome = prov.provision(
        name="Test Client",
        email="client@example.com",
        password_hash="x",
        locale="de",
        country="DE",
    )
    assert account.customer_id == card.customer_id
    assert card.business_id.startswith("VC-")
    support = SupportCenterService(tmp_path)
    hits = support.lookup(card.business_id)
    assert len(hits) == 1
    assert hits[0]["email"] == "client@example.com"
    full = support.build_client_card(card.customer_id)
    assert full is not None
    assert full["business_id"] == card.business_id
    assert any(e["kind"] == "registered" for e in full["timeline"])


def test_support_note_and_ticket(tmp_path: Path):
    prov = CustomerProvisioner(tmp_path)
    _, card, _, _ = prov.provision(
        name="Note Client",
        email="note@example.com",
        password_hash="x",
    )
    support = SupportCenterService(tmp_path)
    note = support.add_note(card.customer_id, "Helped with Stripe connect")
    assert note is not None
    ticket = support.create_ticket(card.customer_id, subject="SMTP setup", body="Cannot send")
    assert ticket is not None
    assert ticket["ticket_id"].startswith("SUP-")
    full = support.build_client_card(card.customer_id)
    assert full is not None
    assert len(full["support"]["notes"]) >= 1
    assert len(full["support"]["tickets"]) >= 1


def test_launch_readiness_includes_client_card(tmp_path: Path):
    out = build_launch_readiness(tmp_path)
    by_id = {i["id"]: i for i in out["items"]}
    assert "client_card" in by_id
    assert by_id["client_card"]["status"] == "done"
    assert by_id["performance"]["status"] == "pending"
    assert out["next"]["id"] == "performance"
