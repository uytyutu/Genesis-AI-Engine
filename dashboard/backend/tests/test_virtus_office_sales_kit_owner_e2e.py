"""Sales Kit Owner E2E — integrated path; LIVE on."""

from __future__ import annotations

from pathlib import Path

from app.integration.virtus_office.b2b_packages import SALES_KIT_LIVE
from app.integration.virtus_office.office_job_ssot import OFFICE_SELLABLE_NOW
from app.integration.virtus_office.sales_kit_owner_e2e import run_owner_e2e
from app.integration.virtus_office.sku_sales_kit import SKU_ENABLED


def test_sales_kit_owner_e2e_integrated(tmp_path: Path):
    report = run_owner_e2e(memory_dir=tmp_path)
    assert report["LIVE"]["SALES_KIT_LIVE"] is True
    assert report["LIVE"]["SKU_ENABLED"] is True
    assert report["OFFICE_SELLABLE_NOW"] == "LIVE_WITH_SALES_KIT"
    assert report["PAYMENT_E2E"] == "PENDING"
    assert SALES_KIT_LIVE is True
    assert SKU_ENABLED is True
    assert "sales_kit_business" in OFFICE_SELLABLE_NOW

    for tier in ("BASIC", "BUSINESS", "PROFESSIONAL"):
        row = report["SALES_KIT_OWNER_E2E"][tier]
        for key in ("input", "execute", "validate", "package", "cabinet", "email", "delivery"):
            assert row[key] == "PASS", (tier, key, report["tier_details"][tier])

    for key, val in report["FAILURE_TESTS"].items():
        assert val == "PASS", (key, report["FAILURE_TESTS"])

    assert report["OWNER_E2E"] == "PASS"
    assert report["FINAL_VERDICT"] == "OWNER_E2E=PASS"
