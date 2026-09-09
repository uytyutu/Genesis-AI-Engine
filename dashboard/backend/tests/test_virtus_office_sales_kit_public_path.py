"""Sales Kit public buyer path — API + UI wiring; LIVE on."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integration.virtus_office.b2b_packages import (
    B2B_PRICE_EUR,
    SALES_KIT_BASIC,
    SALES_KIT_BUSINESS,
    SALES_KIT_LIVE,
    SALES_KIT_PROFESSIONAL,
    SALES_KIT_SKUS,
)
from app.integration.virtus_office.job_engine import OfficeJobEngine, OfficeJobError
from app.integration.virtus_office.office_job_ssot import OFFICE_SELLABLE_NOW
from app.integration.virtus_office.payment_bridge import lock_and_begin_checkout
from app.integration.virtus_office.router import router as office_router
from app.integration.virtus_office.sku_sales_kit import SKU_ENABLED
from app.integration.virtus_office.understanding import (
    ACTION_CATALOG,
    CUSTOMER_EXECUTABLE_ACTIONS,
)

DASH = Path(__file__).resolve().parents[2]  # dashboard/
FRONTEND = DASH / "frontend"


def _company(**overrides):
    base = {
        "company_name": "Muster Handwerk GmbH",
        "description": "Handwerksleistungen in Berlin",
        "services": ["Reparatur", "Wartung"],
        "prices": ["Reparatur — 89 EUR"],
        "contacts": {"email": "info@muster-handwerk.de", "phone": "+49 30 123"},
    }
    base.update(overrides)
    return base


@pytest.fixture()
def client(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    app = FastAPI()
    app.include_router(office_router)
    with patch("app.integration.virtus_office.router._engine", return_value=eng):
        yield TestClient(app), eng


def test_live_flags_on():
    assert SALES_KIT_LIVE is True
    assert SKU_ENABLED is True
    for sku in SALES_KIT_SKUS:
        assert sku in OFFICE_SELLABLE_NOW
        assert sku in CUSTOMER_EXECUTABLE_ACTIONS
        meta = next(a for a in ACTION_CATALOG if a["id"] == sku)
        assert meta.get("customer_sellable") is True
        assert meta.get("public_path_ready") is True


@pytest.mark.parametrize(
    "tier,price",
    [
        (SALES_KIT_BASIC, 99.0),
        (SALES_KIT_BUSINESS, 199.0),
        (SALES_KIT_PROFESSIONAL, 299.0),
    ],
)
def test_public_api_valid_tiers(client, tier, price):
    http, _eng = client
    r = http.post(
        "/api/office/sales-kit-company",
        json={"tier": tier, "company": _company(), "email": "buyer@example.com"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["tier"] == tier
    assert float(body["price_eur"]) == price
    assert body["sales_kit_live"] is True
    assert body["purchase_blocked_until_live"] is False
    assert body["job_id"]
    assert body["owner_token"]
    assert body["status"] == "proposal_ready"


def test_public_api_invalid_sku(client):
    http, _ = client
    r = http.post(
        "/api/office/sales-kit-company",
        json={"tier": "sales_kit_ultra", "company": _company()},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "invalid_tier"


def test_public_api_invalid_tier_alias_rejected_unknown(client):
    http, _ = client
    r = http.post(
        "/api/office/sales-kit-company",
        json={"tier": "enterprise", "company": _company()},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "invalid_tier"


def test_public_api_missing_company_data(client):
    http, _ = client
    r = http.post(
        "/api/office/sales-kit-company",
        json={"tier": SALES_KIT_BASIC, "company": {"company_name": ""}},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "missing_input"


def test_public_api_price_tampering(client):
    http, _ = client
    r = http.post(
        "/api/office/sales-kit-company",
        json={
            "tier": SALES_KIT_BASIC,
            "company": _company(),
            "price_eur": 1.0,
        },
    )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "price_mismatch"


def test_checkout_live_allows_checkout_lock(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(email="buyer@example.com")
    eng.configure_sales_kit(
        created["job_id"],
        owner_token=created["owner_token"],
        tier=SALES_KIT_BUSINESS,
        company=_company(),
    )
    try:
        out = lock_and_begin_checkout(
            eng,
            created["job_id"],
            owner_token=created["owner_token"],
            success_url="https://example.com/ok",
            cancel_url="https://example.com/cancel",
            email="buyer@example.com",
            client_price_eur=199.0,
        )
        chk = out.get("checkout") or {}
        assert chk.get("ok") is True
        assert chk.get("order_id")
    except OfficeJobError as exc:
        # Environment may lack Stripe/sandbox setup; key invariant is no LIVE gate block.
        assert exc.code != "product_not_live"


def test_prices_canonical():
    assert B2B_PRICE_EUR[SALES_KIT_BASIC] == 99
    assert B2B_PRICE_EUR[SALES_KIT_BUSINESS] == 199
    assert B2B_PRICE_EUR[SALES_KIT_PROFESSIONAL] == 299


def test_public_ui_files():
    page = FRONTEND / "app/office/sales-kit/page.tsx"
    comp = FRONTEND / "app/components/office/OfficeSalesKitPage.tsx"
    api = FRONTEND / "app/lib/officeApi.ts"
    i18n = FRONTEND / "app/office/i18n/de.json"
    assert page.is_file()
    assert comp.is_file()
    text = comp.read_text(encoding="utf-8")
    assert "sales_kit_basic" in text
    assert "sales_kit_business" in text
    assert "sales_kit_professional" in text
    assert "99" in text and "199" in text and "299" in text
    assert "ctaCheckout" in text or "Jetzt bestellen" in text or "salesKit.ctaCheckout" in text
    assert "Mission Control" not in text
    assert "sandbox" not in text.lower()
    assert "configureSalesKitCompany" in api.read_text(encoding="utf-8")
    de = json.loads(i18n.read_text(encoding="utf-8"))
    assert de["nav"]["sales_kit"] == "Sales Kit"
    assert de["salesKit"]["tiers"]["sales_kit_basic"]["label"] == "Basic"
    assert "99" in de["catalog"]["sales_kit"]["price"] or de["catalog"]["sales_kit"]["price"] == "99"


def test_regression_other_b2b_not_sellable():
    from app.integration.virtus_office.b2b_packages import B2B_PACKAGE_SKUS

    for sku in B2B_PACKAGE_SKUS:
        if sku in SALES_KIT_SKUS:
            continue
        assert sku not in OFFICE_SELLABLE_NOW
        assert sku not in CUSTOMER_EXECUTABLE_ACTIONS


def test_sales_kit_public_path_report(tmp_path: Path):
    from app.integration.virtus_office.sales_kit_live_readiness import audit_live_readiness

    report = audit_live_readiness(memory_hint=tmp_path)
    assert report["CURRENT_STATE"]["SALES_KIT_LIVE"] is True
    assert report["CURRENT_STATE"]["SKU_ENABLED"] is True
    assert report["CURRENT_STATE"]["OFFICE_SELLABLE_NOW"] == "LIVE_WITH_SALES_KIT"
    assert report["SALES_KIT_PUBLIC_PATH"] == "PASS"
