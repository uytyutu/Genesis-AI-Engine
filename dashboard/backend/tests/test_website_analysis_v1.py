"""Website Analysis v1 — owner report + Repair/New funnel."""

from __future__ import annotations

from pathlib import Path

from app.integration.website_analysis_v1 import (
    ENGINE_ID,
    PRICE_BUSINESS,
    PRICE_REPAIR_LITE,
    WebsiteAnalysisV1,
    build_owner_report,
    compute_repair_quote,
)


def test_report_from_healthy_flags():
    raw = {
        "url": "https://example.com",
        "final_url": "https://example.com",
        "title": "Example Shop",
        "load_ms": 800,
        "has_https": True,
        "has_viewport": True,
        "flags": {
            "has_contact": True,
            "has_form": True,
            "has_cta": True,
            "has_maps": False,
            "content_thin": False,
        },
        "issues": [],
        "strengths": [],
        "analyzed_at": "2026-07-23T00:00:00+00:00",
        "error": None,
    }
    report = build_owner_report(raw, locale="en")
    assert report["engine"] == ENGINE_ID
    assert report["principle"] == "Solve Digital Problems"
    assert 0 <= report["health_score"] <= 100
    assert report["health_score"] >= 70
    maps = next(c for c in report["checks"] if c["id"] == "maps")
    assert maps["status"] == "fail"
    rec_ids = [r["id"] for r in report["recommendations"]]
    assert "repair" in rec_ids and "new_business" in rec_ids
    business = next(r for r in report["recommendations"] if r["id"] == "new_business")
    assert business["availability"] == "available"
    assert business["cta"] == "order_now"
    assert "350" in business["price_label"] or "1200" in business["price_label"]
    repair = next(r for r in report["recommendations"] if r["id"] == "repair")
    assert repair["cta"] == "order_now"
    assert repair["availability"] == "available"
    assert repair["cta_href"] and "repair_" in repair["cta_href"]
    assert "operator" not in (repair.get("summary") or "").lower()
    assert "auto-cms" not in (repair.get("summary") or "").lower()
    assert report.get("vector_plain")
    assert report.get("repair_quote", {}).get("price_eur")


def test_german_recommendations_use_reparatur():
    raw = {
        "url": "https://example.de",
        "final_url": "https://example.de",
        "title": "Shop",
        "load_ms": 900,
        "has_https": True,
        "has_viewport": True,
        "flags": {
            "has_contact": True,
            "has_form": False,
            "has_cta": True,
            "has_maps": True,
            "content_thin": False,
        },
        "issues": [],
        "strengths": [],
        "analyzed_at": "2026-07-23T00:00:00+00:00",
        "error": None,
    }
    report = build_owner_report(raw, locale="de")
    repair = next(r for r in report["recommendations"] if r["id"] == "repair")
    assert "Reparatur" in repair["title"]
    assert "Operator" not in repair["summary"]
    assert "Fake" not in report["justification"]
    assert "Eindruck" in report["vector_plain"] or "empfehl" in report["vector_plain"].lower()


def test_unreachable_marks_unavailable_checks():
    raw = {
        "url": "https://bad.example",
        "final_url": "https://bad.example",
        "title": "",
        "load_ms": 0,
        "has_https": False,
        "has_viewport": False,
        "issues": ["unreachable"],
        "strengths": [],
        "error": "fetch_failed",
        "analyzed_at": "2026-07-23T00:00:00+00:00",
    }
    report = build_owner_report(raw)
    assert report["health_score"] == 0
    unavailable = [c for c in report["checks"] if c["status"] == "unavailable"]
    assert len(unavailable) >= 3
    assert "недоступ" in report["justification"].lower() or "доступ" in report["justification"].lower()
    new = next(r for r in report["recommendations"] if r["id"] == "new_business")
    assert new.get("recommended") is True


def test_repair_quote_lite_for_few_fails():
    q = compute_repair_quote(health_score=80, fail_n=1, fetch_ok=True)
    assert q["package_id"] == "repair_lite"
    assert q["price_eur"] == PRICE_REPAIR_LITE
    assert q["prefer_new"] is False


def test_service_invalid_url(tmp_path: Path):
    out = WebsiteAnalysisV1(tmp_path).analyze("not a url", use_cache=False, save_case=False)
    assert out["engine"] == ENGINE_ID
    assert out["health_score"] == 0 or out.get("error")


def test_analysis_case_saved(tmp_path: Path):
    raw_ok = {
        "url": "https://shop.example",
        "final_url": "https://shop.example",
        "title": "Shop",
        "load_ms": 500,
        "has_https": True,
        "has_viewport": True,
        "flags": {
            "has_contact": True,
            "has_form": True,
            "has_cta": True,
            "has_maps": True,
            "content_thin": False,
        },
        "analyzed_at": "2026-07-23T00:00:00+00:00",
        "error": None,
    }
    from app.integration.website_analysis_v1 import AnalysisCaseStore, build_owner_report

    report = build_owner_report(raw_ok)
    store = AnalysisCaseStore(tmp_path)
    meta = store.save(report, email="Owner@Example.DE", problem_note="slow")
    assert meta["case_id"].startswith("an-")
    listed = store.list_for_email("owner@example.de")
    assert len(listed) == 1
    assert listed[0]["case_id"] == meta["case_id"]
