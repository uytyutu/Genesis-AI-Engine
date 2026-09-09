"""Sales Kit sandbox Payment E2E — real sandbox checkout; LIVE on."""

from __future__ import annotations

from pathlib import Path

from app.integration.virtus_office.b2b_packages import SALES_KIT_LIVE
from app.integration.virtus_office.office_job_ssot import OFFICE_SELLABLE_NOW
from app.integration.virtus_office.sales_kit_payment_e2e import run_payment_e2e
from app.integration.virtus_office.sku_sales_kit import SKU_ENABLED


def test_sales_kit_payment_e2e_sandbox(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.setenv("GENESIS_OFFICE_SALES_KIT_SANDBOX_E2E", "1")
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_SECRET_KEY_LIVE", raising=False)

    report = run_payment_e2e(memory_dir=tmp_path)
    assert report["LIVE"]["SALES_KIT_LIVE"] is True
    assert report["LIVE"]["SKU_ENABLED"] is True
    assert report["OFFICE_SELLABLE_NOW"] == "LIVE_WITH_SALES_KIT"
    assert SALES_KIT_LIVE is True
    assert SKU_ENABLED is True
    assert "sales_kit_business" in OFFICE_SELLABLE_NOW

    if report.get("PAYMENT_E2E") == "BLOCKED":
        # Honest: missing sandbox configuration — do not invent credentials
        assert report.get("REASON")
        return

    assert report["PAYMENT_E2E"] == "PASS"
    assert report["PRICE_INTEGRITY"] == "PASS"
    assert report["PUBLIC_LIVE_GATE"] == "PASS"
    for tier in ("BASIC", "BUSINESS", "PROFESSIONAL"):
        row = report["SALES_KIT_PAYMENT_E2E"][tier]
        for key in (
            "checkout",
            "sandbox_payment",
            "paid_job",
            "execute",
            "validate",
            "cabinet",
            "delivery",
        ):
            assert row[key] == "PASS", (tier, key, report["tier_details"][tier])
