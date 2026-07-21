"""Lead Priority — commercial value ranking (soft BP + hunt-ready niches)."""

from app.integration.lead_commercial_value import (
    compute_lead_priority,
    recommend_package_id,
    score_business_potential,
    score_website_need,
)
from app.integration.outreach_hunt_rotation import niches_for_language


def test_hunt_niches_include_high_ltv_professions():
    de = niches_for_language("de")
    en = niches_for_language("en-us")
    for needle in ("Rechtsanwalt", "Photovoltaik", "Steuerberater", "Immobilienmakler"):
        assert any(needle.lower() in n.lower() for n in de), de
    for needle in ("law firm", "solar", "accountant", "real estate"):
        assert any(needle in n.lower() for n in en), en
    assert len(de) >= 10 and len(en) >= 10


def test_bare_dental_without_signals_not_auto_premium():
    """Industry prior alone must stay below Premium gate."""
    row = {
        "company_name": "Zahnarzt Müller",
        "website_url": "https://zahn-mueller.example",
        "fit_reason": "Google Places",
        "meta": {"niche": "zahnarzt"},
        "site_analysis": {"issue_count": 2, "issues": ["SEO", "Langsam"]},
    }
    bp, reasons = score_business_potential(row, analysis=row["site_analysis"])
    assert bp < 0.78, (bp, reasons)
    pkg, _ = recommend_package_id(bp, 0.55)
    assert pkg in ("basic", "business")


def test_dental_with_strong_signals_can_reach_premium():
    row = {
        "company_name": "Zahnklinik Nord GmbH",
        "website_url": "https://zahnklinik-nord.de",
        "fit_reason": "Google Places",
        "meta": {"niche": "zahnarzt", "review_count": 520, "rating": 4.6, "types": "dentist"},
        "site_analysis": {"issue_count": 2, "issues": ["SEO Titel fehlt", "Langsame Seite"]},
    }
    bp, _ = score_business_potential(row, analysis=row["site_analysis"])
    wn, _ = score_website_need(row, row["site_analysis"])
    pkg, rationale = recommend_package_id(bp, wn)
    assert bp >= 0.78
    assert pkg == "premium"
    assert "Premium" in rationale


def test_plumber_high_win_below_signaled_clinic():
    plumber = {
        "company_name": "Hans Klempner",
        "website_url": "https://hans-rohr.de",
        "fit_reason": "Google Places: слабый сайт",
        "meta": {"niche": "plumber", "hunt_query": "Sanitär", "review_count": 2},
        "site_analysis": {
            "issue_count": 5,
            "issues": ["HTTPS", "Mobil", "Kontakt", "SEO", "Veraltet"],
            "improvement_score": 80,
        },
    }
    clinic = {
        "company_name": "Dental Care Clinic GmbH",
        "website_url": "https://dental-care.example",
        "fit_reason": "Google Places",
        "meta": {"niche": "zahnarzt", "review_count": 400, "rating": 4.5, "types": "dentist"},
        "site_analysis": {"issue_count": 2, "issues": ["SEO", "Langsam"]},
    }
    p_pl = compute_lead_priority(plumber, win_probability_pct=90)
    p_cl = compute_lead_priority(clinic, win_probability_pct=40)
    assert p_cl["recommended_package_id"] == "premium"
    assert p_cl["lead_priority"] > p_pl["lead_priority"]


def test_unreachable_premium_not_always_on_top():
    row = {
        "company_name": "Premium Autohaus AG",
        "website_url": "https://autohaus.example",
        "meta": {"niche": "auto_dealer", "review_count": 800, "rating": 4.7, "types": "car_dealer"},
        "site_analysis": {"issue_count": 1, "issues": ["SEO"]},
    }
    low_win = compute_lead_priority(row, win_probability_pct=5)
    mid = {
        "company_name": "Dachdecker Müller",
        "website_url": "",
        "fit_reason": "нет сайта",
        "meta": {"niche": "dach"},
        "site_analysis": {},
    }
    mid_win = compute_lead_priority(mid, win_probability_pct=55)
    assert mid_win["lead_priority"] > low_win["lead_priority"]
