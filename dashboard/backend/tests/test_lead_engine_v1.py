"""Lead Engine v1 — Business Time (24/7), Premium Score, Smart Offer, Quality Gate."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.integration.business_time import is_business_hours, business_time_status
from app.integration.lead_engine_premium import (
    apply_premium_and_offer,
    compute_premium_score,
    select_smart_offer,
)
from app.integration.lead_engine_quality_gate import quality_gate_before_send
from app.integration.lead_engine_queues import build_lead_engine_dashboard, classify_lead_queue
from app.integration.acquisition_studio_service import AcquisitionStudioService
import pytest



class _Opp:
    def __init__(self, rows: list[dict]):
        self._rows = rows
        self.memory_dir = Path(".")

    def _load_rows(self):
        return list(self._rows)

    def list_opportunities(self, limit: int = 200):
        return list(self._rows)[:limit]

    def get(self, oid: str):
        for r in self._rows:
            if r.get("id") == oid:
                return r
        return None

    def _save_rows(self, rows):
        self._rows = list(rows)


def test_business_hours_always_24_7():
    """CEO 2026-07-30: no weekday 09-18 gate — always open."""
    utc_night = datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
    utc_weekend = datetime(2026, 7, 25, 10, 0, tzinfo=timezone.utc)
    assert is_business_hours("DE", now_utc=utc_night) is True
    assert is_business_hours("DE", now_utc=utc_weekend) is True
    assert is_business_hours("US", now_utc=utc_night) is True
    assert is_business_hours("JP", now_utc=utc_night) is True
    st = business_time_status("DE", now_utc=utc_night)
    assert st["open"] is True
    assert st["window"] == "24/7"
    assert st["business_hours_enforced"] is False


def test_apac_language_packs():
    from app.integration.outreach_language_service import (
        OutreachLanguageService,
        language_for_market,
    )
    from app.integration.country_profiles import DEFAULT_ENABLED, TIER_APAC

    assert language_for_market("JP") == "ja"
    assert language_for_market("KR") == "ko"
    assert language_for_market("AU") == "en-us"
    assert language_for_market("NZ") == "en-us"
    assert language_for_market("SG") == "en-us"
    for code in TIER_APAC:
        assert code in DEFAULT_ENABLED

    svc = OutreachLanguageService()
    for market, lang in (("JP", "ja"), ("KR", "ko"), ("AU", "en-us")):
        subject, body, used = svc.draft_outreach(
            company="Test Co",
            analysis={"issues": ["mobile"]},
            package={"name": "Basic", "price_label": "X"},
            price=100,
            fit_reason="test",
            language=lang,
            row={"market": market, "meta": {"market": market}},
            allow_llm=False,
        )
        assert used == lang
        assert subject
        assert "Virtus Core" in body or "Test Co" in body


def test_apac_markets_enabled_in_json():
    from app.integration.outreach_market_config import reload_outreach_markets, get_market

    reload_outreach_markets()
    for code in ("AU", "NZ", "JP", "KR", "SG"):
        m = get_market(code)
        assert m is not None, code
        assert m.get("enabled") is True, code
        assert m.get("template"), code


def test_premium_score_no_website():
    row = {"website_url": "", "fit_reason": "нет сайта", "meta": {}}
    prem = compute_premium_score(row)
    assert prem["premium_score"] >= 40
    assert "no_website" in prem["signals"]


def test_smart_offer_no_site_basic():
    row = {"website_url": "", "fit_reason": "no website", "meta": {}}
    offer = select_smart_offer(row)
    assert offer["recommended_package_id"] == "basic"
    assert not offer["skip_outreach"]


def test_smart_offer_broken_repair():
    row = {
        "website_url": "https://ex.example",
        "meta": {},
        "site_analysis": {
            "fetch_ok": False,
            "issues": ["unreachable", "timeout"],
            "issue_count": 8,
        },
    }
    offer = select_smart_offer(row)
    assert offer["offer_kind"] == "repair"
    assert str(offer["recommended_package_id"]).startswith("repair")


def test_smart_offer_healthy_skip():
    row = {
        "website_url": "https://modern.example",
        "meta": {},
        "site_analysis": {
            "fetch_ok": True,
            "issues": [],
            "issue_count": 0,
            "improvement_score": 10,
        },
    }
    offer = select_smart_offer(row)
    assert offer["skip_outreach"] is True
    assert offer["skip_reason"] == "healthy_site"


def test_quality_gate_invalid_email():
    row = {
        "contact": "not-an-email",
        "proposed_message": "Hi",
        "meta": {"market": "DE"},
        "outreach_status": "approved",
    }
    # Force open hours
    utc = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
    gate = quality_gate_before_send(row, now_utc=utc)
    assert gate["ok"] is False
    assert gate["reason"] == "invalid_email"


def test_quality_gate_night_still_passes_hours():
    row = {
        "contact": "a@b.com",
        "proposed_message": "Hi",
        "recommended_package_id": "basic",
        "meta": {"market": "DE"},
        "outreach_status": "approved",
    }
    utc = datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)  # 22:00 Berlin
    gate = quality_gate_before_send(row, now_utc=utc)
    # Hours gate removed — may still fail CCI / other quality checks, never hours.
    assert gate.get("reason") != "outside_business_hours"


def test_fresh_archive_keeps_sent(tmp_path: Path):
    rows = [
        {
            "id": "a",
            "status": "new",
            "outreach_status": "pending_approval",
            "company_name": "Old Draft",
            "meta": {},
            "interactions": [],
        },
        {
            "id": "b",
            "status": "contacted",
            "outreach_status": "sent",
            "company_name": "Sent Co",
            "meta": {},
            "interactions": [],
        },
        {
            "id": "c",
            "status": "won",
            "outreach_status": "sent",
            "company_name": "Won Co",
            "meta": {},
            "interactions": [],
        },
    ]
    svc = AcquisitionStudioService.__new__(AcquisitionStudioService)
    svc._memory_dir = tmp_path
    svc._opportunity = _Opp(rows)

    def _replace(oid, row):
        out = []
        for r in svc._opportunity._rows:
            out.append(row if r.get("id") == oid else r)
        return out

    svc._replace_row = _replace
    svc._log_interaction = lambda *a, **k: None
    svc._archive_quality = AcquisitionStudioService._archive_quality.__get__(svc)
    result = svc.archive_stale_pipeline_for_fresh_run()
    assert result["kept_sent_or_closed"] >= 2
    saved = svc._opportunity._rows
    assert saved[0]["meta"].get("quality_archive") is True
    assert not saved[1]["meta"].get("quality_archive")
    assert not saved[2]["meta"].get("quality_archive")


def test_dashboard_ready_waiting_split():
    utc = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
    rows = [
        {
            "id": "1",
            "company_name": "Ready Co",
            "contact": "info@ready-co.de",
            "website_url": "https://ready-co.de",
            "proposed_message": "Hi",
            "outreach_status": "approved",
            "status": "new",
            "found_at": "2026-07-20T09:00:00+00:00",
            "recommended_package_id": "basic",
            "meta": {"market": "DE", "premium_score": 55},
            "site_analysis": {"fetch_ok": True, "emails_found": ["info@ready-co.de"]},
        },
        {
            "id": "2",
            "company_name": "Sent Co",
            "contact": "b@b.de",
            "outreach_status": "sent",
            "status": "contacted",
            "meta": {"market": "DE", "premium_score": 10},
        },
    ]
    dash = build_lead_engine_dashboard(rows, now_utc=utc, enabled_markets=["DE"])
    assert dash["ready_now"] >= 1
    assert dash["history"] >= 1
    assert dash["countries"][0]["market"] == "DE"
    assert dash["countries"][0]["window"] == "24/7"


def test_apply_premium_mutates_meta():
    row = {"website_url": "", "fit_reason": "no website", "meta": {}}
    offer = apply_premium_and_offer(row)
    assert row["meta"]["premium_score"] >= 40
    assert offer["recommended_package_id"] == "basic"
