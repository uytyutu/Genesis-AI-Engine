"""Product direction — intent-aware actions after document analysis."""

from __future__ import annotations

from app.execution.post_analysis_actions import (
    build_analysis_completion_message,
    suggest_post_analysis_actions,
)


def test_business_plan_actions_include_site_not_only():
    actions = suggest_post_analysis_actions(
        doc_type="business_plan",
        locale="ru",
        summary_href="/summary",
        conclusion_href="/conclusion",
        site_available=True,
    )
    labels = [a["label"] for a in actions]
    assert any("сайт" in l.lower() for l in labels)
    assert any("Executive Summary" in l for l in labels)
    assert any("заключение" in l.lower() or "Бизнес" in l for l in labels)
    assert any(a.get("available") is False for a in actions)


def test_financial_report_no_site_by_default():
    actions = suggest_post_analysis_actions(
        doc_type="financial_report",
        locale="en",
        summary_href="/s",
        conclusion_href="/c",
        site_available=True,
    )
    labels = " ".join(a["label"] for a in actions)
    assert "website" not in labels.lower() or "soon" in labels.lower()


def test_completion_message_honest_no_fake_fixes():
    msg = build_analysis_completion_message(
        locale="ru",
        doc_type="business_plan",
        source_name="plan.pdf",
        readiness=62,
        issues_count=5,
        priority_count=4,
    )
    assert "62/100" in msg
    assert "5" in msg
    assert "исправил" not in msg.lower()
