"""Business Language Engine — forbid generic AI phrases on beauty copy."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from app.factory.business_language import (
    assert_niche_language,
    build_beauty_lumia_brief,
    find_forbidden_hits,
    resolve_voice,
)


def test_beauty_voice_resolves_from_nail_studio():
    v = resolve_voice("nail_studio")
    assert v.industry_id == "beauty_nail_brow_massage"
    assert "Maniküre" in v.lexicon or any("Maniküre" in s[0] for s in v.service_examples)


def test_forbidden_audit_on_beauty_copy():
    hits = find_forbidden_hits("Unser Audit und Support für Ihr Business")
    assert "audit" in hits
    assert "support" in hits


def test_lumia_brief_has_concrete_services():
    brief = build_beauty_lumia_brief()
    titles = [s["title"] for s in brief.services]
    assert any("Maniküre" in t for t in titles)
    assert not any(t.lower() in {"audit", "support", "workshop"} for t in titles)
    blob = brief.hero_headline + brief.hero_sub + brief.about_body
    assert not assert_niche_language(blob, "nail_studio")
