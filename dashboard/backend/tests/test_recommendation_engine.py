"""Recommendation Engine — need-gated multi-source offers."""

from pathlib import Path

from app.recommendation_engine.catalog import load_offers
from app.recommendation_engine.engine import build_recommended_solutions, public_solutions_only
from app.recommendation_engine.needs import detect_confirmed_needs
from app.commercial_api.sanitize import sanitize_public


def test_needs_only_when_markers_absent():
    html_gap = (
        "<html><body><h1>Local Salon Berlin</h1>"
        "<p>Welcome to our studio. Call us for appointments and hair care.</p>"
        "<p>We love our customers every day of the week.</p></body></html>"
    )
    needs = detect_confirmed_needs(html=html_gap, fetch_ok=True)
    ids = {n["id"] for n in needs}
    assert "crm" in ids
    assert "online_booking" in ids
    assert "email_marketing" in ids

    html_crm = html_gap + '<script src="https://js.hubspot.com/x.js"></script>'
    needs2 = detect_confirmed_needs(html=html_crm, fetch_ok=True)
    assert "crm" not in {n["id"] for n in needs2}


def test_no_recommend_without_need_match(tmp_path: Path):
    # Need confirmed but we only pass empty needs list → no solutions
    block = build_recommended_solutions(
        confirmed_needs=[],
        memory_dir=tmp_path,
        audience="client",
    )
    assert block["solutions"] == []


def test_recommend_only_for_confirmed_need(tmp_path: Path):
    html = (
        "<html><body><h1>Local business site</h1>"
        "<p>Services and contact information for our customers in the city center.</p>"
        "</body></html>"
    )
    needs = detect_confirmed_needs(html=html, fetch_ok=True)
    block = build_recommended_solutions(
        confirmed_needs=needs,
        memory_dir=tmp_path,
        locale="ru",
        audience="client",
    )
    assert block["count"] >= 1
    for s in block["solutions"]:
        assert s["official_url"].startswith("http")
        assert "commission" not in s
        assert "ceo_only" not in s
        assert s["why"]


def test_owner_audience_has_ceo_only_not_in_public(tmp_path: Path):
    needs = [{"id": "crm", "confirmed": True, "label_ru": "CRM", "why_ru": "нет CRM", "label_en": "CRM", "why_en": "no crm"}]
    owner = build_recommended_solutions(
        confirmed_needs=needs,
        memory_dir=tmp_path,
        audience="owner",
    )
    assert owner["solutions"][0].get("ceo_only")
    pub = public_solutions_only(owner)
    assert pub is not None
    assert "ceo_only" not in pub["solutions"][0]
    cleaned = sanitize_public(owner)
    assert "ceo_only" not in str(cleaned)


def test_catalog_has_multiple_sources():
    offers = load_offers()
    sources = {o["source_id"] for o in offers}
    assert "digistore24" in sources
    assert "virtus_core" in sources
    assert "partner_a" in sources
