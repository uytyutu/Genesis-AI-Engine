"""Commercial Acceptance + UX Quality gates."""

from app.integration.commercial_acceptance_gate import (
    audit_ux_quality_html,
    build_commercial_acceptance_gate,
)


def test_ux_empty_button_fails():
    html = '<html><body><button class="cta"></button><a href="#contact">Go</a><div id="contact"></div></body></html>'
    out = audit_ux_quality_html(html, label="t")
    assert out["ok"] is False
    assert any("empty <button>" in i for i in out["issues"])


def test_ux_dead_anchor_fails():
    html = '<html><body><a href="#missing">x</a></body></html>'
    out = audit_ux_quality_html(html, label="t")
    assert out["ok"] is False
    assert any("dead anchor" in i for i in out["issues"])


def test_commercial_acceptance_shape():
    out = build_commercial_acceptance_gate()
    assert out["id"] == "commercial_acceptance_gate"
    assert out["items"]
    assert any(i["id"] == "ceo_blind_test" and i["auto"] is True for i in out["items"])
    assert any(i["id"] == "commercial_readiness" for i in out["items"])
    assert any(i["id"] == "premium_wow" for i in out["items"])
    assert "ceo_blind_test" in out
    assert "commercial_readiness" in out
    assert "Commercial Readiness" in out["policy_ru"] or "цифров" in out["policy_ru"]
