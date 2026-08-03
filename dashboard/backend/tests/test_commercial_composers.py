"""Commercial composers + Hard Gate / AI Score."""

from __future__ import annotations

from app.factory.analyzer import analyze
from app.factory.composers import COMPOSER_IDS, run_composers
from app.factory.composers.quality import run_commercial_gate
from app.factory.composers.context import context_from_contacts
from app.factory.industry_scenarios import resolve_scenario


def test_composer_ids_locked():
    assert "quality_gate" in COMPOSER_IDS
    assert "hero" in COMPOSER_IDS
    assert len(COMPOSER_IDS) >= 10


def test_hard_gate_blocks_partner_chrome():
    analysis = analyze("Nordlicht GmbH — regionale Beratung")
    # Force banned headline
    from dataclasses import replace

    bad = replace(analysis, headline=f"{analysis.business_name} — Ihr Partner vor Ort")
    ctx = context_from_contacts(
        {"business_name": analysis.business_name, "phone": "+491234", "email": "a@b.de"},
        niche=analysis.niche,
    )
    gate = run_commercial_gate(analysis=bad, ctx=ctx)
    assert not gate.hard_passed
    assert any(c.id == "no_generic_phrases" and not c.ok for c in gate.hard_checks)


def test_run_composers_beauty_vs_auto_differ():
    beauty, g1 = run_composers(
        analyze("Salon Mira Berlin — Haarschnitt Farbe Pflege"),
        contacts={
            "business_name": "Salon Mira",
            "city": "Berlin",
            "phone": "+49111",
            "email": "mira@example.de",
            "services_list": ["Balayage", "Schnitt", "Pflege"],
            "niche": "beauty",
        },
    )
    auto, g2 = run_composers(
        analyze("Autowerkstatt Nord Hamburg — Inspektion Reifen Diagnose"),
        contacts={
            "business_name": "Autowerkstatt Nord",
            "city": "Hamburg",
            "phone": "+49222",
            "email": "nord@example.de",
            "services_list": ["Diagnose", "Inspektion", "Reifen"],
            "niche": "auto",
        },
    )
    assert beauty.niche == "beauty"
    assert auto.niche == "auto"
    assert beauty.headline != auto.headline
    assert beauty.cta_label != auto.cta_label or beauty.services != auto.services
    assert resolve_scenario("beauty").layout_bias != resolve_scenario("auto").layout_bias
    assert g1.hard_passed, g1.failures
    assert g2.hard_passed, g2.failures
    # AI Score is secondary — reported even when hard passed
    assert g1.ai_score.overall > 0
    assert "design" in g1.extras


def test_questionnaire_services_win():
    base = analyze("Salon Mira Berlin — Haarschnitt")
    out, gate = run_composers(
        base,
        contacts={
            "business_name": "Salon Mira",
            "phone": "+49111",
            "email": "a@b.de",
            "services_list": ["Wimpernlifting", "Brautstyling", "Balayage"],
        },
    )
    assert out.services[0] == "Wimpernlifting"
    assert gate.hard_passed, gate.failures


def test_score_does_not_override_hard_fail():
    from dataclasses import replace
    from app.factory.composers.quality import AiScore, CommercialGateResult

    # Simulate: high score but hard fail must mean not passed
    r = CommercialGateResult(
        hard_passed=False,
        score_passed=True,
        ai_score=AiScore(
            niche_match=99,
            content_quality=99,
            cta_quality=99,
            structure_quality=99,
            design_quality=99,
            commercial_readiness=99,
        ),
    )
    assert not r.passed
