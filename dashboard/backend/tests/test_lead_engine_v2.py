"""Lead Engine v2 — reset, dedup, priority, contact history, country farms."""

from __future__ import annotations

from pathlib import Path

from app.integration.country_profiles import ALL_PROFILE_CODES, merge_runtime_config
from app.integration.lead_engine_v2 import (
    LeadEngineV2,
    normalize_domain,
    priority_from_analysis,
    reasons_from_analysis,
)


def test_normalize_domain():
    assert normalize_domain("https://www.Example.de/path") == "example.de"


def test_reasons_and_priority():
    analysis = {
        "health_score": 40,
        "checks": [
            {"id": "https", "label": "HTTPS", "status": "fail", "detail": "No HTTPS"},
            {"id": "cta", "label": "CTA", "status": "fail", "detail": "No CTA"},
            {"id": "mobile", "label": "Mobile", "status": "pass", "detail": "ok"},
        ],
        "problems": [],
    }
    reasons = reasons_from_analysis(analysis)
    assert any(r["code"] == "https" for r in reasons)
    assert priority_from_analysis(analysis, reasons=reasons) == "High"


def test_domain_dedup_ignores_city_niche(tmp_path: Path):
    eng = LeadEngineV2(tmp_path)
    a = eng.ingest_lead(
        {
            "company": "Zahn Praxis",
            "website": "https://zahn.example.de",
            "email": "info@zahn.example.de",
            "country": "DE",
            "city": "Dresden",
            "niche": "Zahnarzt",
            "source": "test",
        },
        analysis={
            "health_score": 55,
            "checks": [
                {"id": "speed", "label": "Speed", "status": "fail", "detail": "slow"},
            ],
        },
    )
    assert a["ok"] is True
    assert a["lead"]["priority"] in ("High", "Medium", "Low")
    assert a["lead"]["reasons"]
    b = eng.ingest_lead(
        {
            "company": "Other Name",
            "website": "https://www.zahn.example.de/x",
            "email": "other@mail.de",
            "country": "AT",
            "city": "Wien",
            "niche": "dentist",
        }
    )
    assert b["ok"] is False
    assert b["reason"] == "domain"


def test_contact_history_blocks_repitch(tmp_path: Path):
    eng = LeadEngineV2(tmp_path)
    eng.record_contact(domain="shop.example.com", email="a@shop.example.com", country="US")
    out = eng.ingest_lead(
        {
            "company": "Shop",
            "website": "https://shop.example.com",
            "email": "b@other.com",
            "country": "US",
        }
    )
    assert out["ok"] is False
    assert out["reason"] == "contacted"


def test_country_profiles_include_cis_and_us():
    cfg = merge_runtime_config(None)
    assert "US" in cfg["enabled_countries"]
    assert "DE" in cfg["enabled_countries"]
    assert "UA" in ALL_PROFILE_CODES and "RU" in ALL_PROFILE_CODES and "KZ" in ALL_PROFILE_CODES
    assert cfg["lead_cap"] is None
    assert cfg["send_interval_min_sec"] == 40
    assert cfg["send_interval_max_sec"] == 60


def test_reset_and_next_slot(tmp_path: Path):
    eng = LeadEngineV2(tmp_path)
    (tmp_path / "opportunities.jsonl").write_text('{"id":"old"}\n', encoding="utf-8")
    out = eng.reset_old_base()
    assert out["ok"] is True
    assert not (tmp_path / "opportunities.jsonl").is_file()
    slot = eng.next_send_slot()
    assert slot["ok"] is True
    assert 40 <= int(slot["wait_sec"]) <= 90
    st = eng.status()
    assert st["version"] == 2
    assert "farms" in st
