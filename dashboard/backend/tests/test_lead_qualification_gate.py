"""Lead qualification gate — checks before outreach."""

from app.integration.lead_qualification_gate import (
    build_audit_report_md,
    discover_contact_channels,
    qualify_lead,
)


def _analysis(**overrides) -> dict:
    base = {
        "status_code": 200,
        "issue_count": 4,
        "issues": ["Kein HTTPS", "Kein Seitentitel", "Langsame Antwort"],
        "title": "Test Shop",
        "emails_found": ["info@test-shop.de"],
    }
    base.update(overrides)
    return base


def _evaluation(**overrides) -> dict:
    base = {
        "win_probability_pct": 72,
        "service_label_ru": "Проверка качества данных",
        "sell_price_eur": 175.0,
        "legal_gate": {"legal": True},
    }
    base.update(overrides)
    return base


def test_qualify_passes_with_email():
    row = {"company_name": "Test Shop", "website_url": "https://test-shop.de", "contact": ""}
    q = qualify_lead(row, _analysis(), evaluation=_evaluation())
    assert q["passed"] is True
    assert q["channels"]["primary_email"] == "info@test-shop.de"


def test_qualify_blocks_dead_site():
    row = {"company_name": "Dead", "website_url": "https://dead.de"}
    q = qualify_lead(
        row,
        _analysis(status_code=0, issue_count=0, issues=[]),
        evaluation=_evaluation(win_probability_pct=30, sell_price_eur=10),
    )
    assert q["passed"] is False
    assert len(q["blockers_ru"]) >= 1


def test_qualify_blocks_wikipedia():
    row = {"company_name": "Wiki", "website_url": "https://www.wikipedia.org"}
    q = qualify_lead(
        row,
        _analysis(status_code=403),
        evaluation=_evaluation(),
    )
    assert q["passed"] is False


def test_audit_report_contains_issues():
    md = build_audit_report_md(
        {"company_name": "ABC", "website_url": "https://abc.de"},
        _analysis(),
        service_label="Аудит сайта",
        price_eur=99.0,
        win_pct=65,
    )
    assert "Аудит сайта" in md
    assert "Kein HTTPS" in md


def test_discover_email_from_analysis():
    ch = discover_contact_channels(contact="", analysis=_analysis())
    assert ch["primary_email"] == "info@test-shop.de"
