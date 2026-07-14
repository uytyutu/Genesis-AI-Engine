from pathlib import Path
from unittest.mock import patch

import pytest

from app.integration.asset_scanner_service import AssetScannerService, assert_public_scan_allowed
from app.integration.opportunity_service import OpportunityService


@pytest.fixture()
def scanner(tmp_path: Path):
    opp = OpportunityService(tmp_path)
    return AssetScannerService(opp)


def test_forbidden_private_targets_blocked():
    with pytest.raises(ValueError, match="forbidden_target"):
        assert_public_scan_allowed("https://bucket.s3.amazonaws.com/private/data")
    with pytest.raises(ValueError, match="forbidden_target"):
        assert_public_scan_allowed("https://example.com/?api_key=secret")


def test_scan_url_creates_asset_opportunity(scanner: AssetScannerService):
    fake_analysis = {
        "url": "https://old-shop.example",
        "final_url": "https://old-shop.example",
        "title": "Old Shop — Under Construction",
        "status_code": 200,
        "issues": ["Anzeichen veralteter Technik oder Baustelle", "Kein viewport"],
        "strengths": ["HTTPS aktiv"],
        "issue_count": 2,
        "improvement_score": 42,
        "error": None,
    }
    with patch(
        "app.integration.asset_scanner_service.SiteAnalysisService.analyze",
        return_value=fake_analysis,
    ):
        row = scanner.scan_url("https://old-shop.example", niche="expired_landing")
    assert row["source_id"] == "asset_scan"
    assert row["opportunity_type"] == "asset"
    assert float(row["potential_value_eur"]) > 0
    assert "Легальный путь" in row["fit_reason"]


def test_accept_for_work_sets_proposed(scanner: AssetScannerService):
    fake_analysis = {
        "url": "https://parked.example",
        "final_url": "https://parked.example",
        "title": "Parked Domain",
        "issues": ["Sehr wenig Inhalt"],
        "strengths": [],
        "issue_count": 3,
        "improvement_score": 30,
    }
    with patch(
        "app.integration.asset_scanner_service.SiteAnalysisService.analyze",
        return_value=fake_analysis,
    ):
        row = scanner.scan_url("https://parked.example")
    accepted = scanner.accept_for_work(row["id"])
    assert accepted["status"] == "proposed"
    assert accepted["meta"].get("monetization") == "pending"
