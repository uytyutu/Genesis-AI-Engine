"""Acceptance: 10 niches must feel like distinct businesses (pre–Meta Ads).

Run:
  py -3.12 -m pytest dashboard/backend/tests/test_acceptance_10_niches.py -q
"""

from __future__ import annotations

from app.factory.analyzer import analyze
from app.factory.composers import run_composers
from app.factory.composers.layout_composer import compose_layout_profile, preferred_layout_ids
from app.factory.composers.context import context_from_contacts
from app.factory.composers.design_composer import compose_design_meta
from app.factory.niche_profiles import resolve_niche_profile

# CEO acceptance set — real SMB niches before Meta Ads.
_CASES: list[dict] = [
    {
        "id": "dental",
        "name": "SmileCare Praxis",
        "city": "München",
        "desc": "SmileCare Praxis München — Zahnarzt, Prophylaxe, Implantate, Ästhetik",
        "niche_hint": "dental",
        "services": ["Prophylaxe", "Implantate", "Bleaching", "Füllungen"],
    },
    {
        "id": "beauty",
        "name": "Salon Mira",
        "city": "Berlin",
        "desc": "Salon Mira Berlin — Haarschnitt, Coloration, Balayage, Pflege",
        "niche_hint": "beauty",
        "services": ["Balayage", "Damenhaarschnitt", "Pflege", "Styling"],
    },
    {
        "id": "auto",
        "name": "Autowerkstatt Nord",
        "city": "Hamburg",
        "desc": "Autowerkstatt Nord Hamburg — Diagnose, Inspektion, Reifen, Ölwechsel",
        "niche_hint": "auto",
        "services": ["Diagnose", "Inspektion", "Reifen", "Ölwechsel"],
    },
    {
        "id": "restaurant",
        "name": "Trattoria Luna",
        "city": "Köln",
        "desc": "Trattoria Luna Köln — Restaurant, Mittagstisch, Abendkarte, Reservierung",
        "niche_hint": "restaurant",
        "services": ["Mittagstisch", "Abendkarte", "Reservierung", "Events"],
    },
    {
        "id": "law",
        "name": "Kanzlei Weber",
        "city": "Frankfurt",
        "desc": "Kanzlei Weber Frankfurt — Anwalt, Familienrecht, Verträge, Beratung",
        "niche_hint": "law",
        "services": ["Erstberatung", "Familienrecht", "Vertragsprüfung", "Vertretung"],
    },
    {
        "id": "accountant",
        "name": "Steuerbüro Klar",
        "city": "Stuttgart",
        "desc": "Steuerbüro Klar Stuttgart — Buchhaltung, Steuererklärung, Jahresabschluss",
        "niche_hint": "accounting",
        "services": ["Buchhaltung", "Steuererklärung", "Jahresabschluss", "Lohnabrechnung"],
    },
    {
        "id": "electrician",
        "name": "Elektro Hoffmann",
        "city": "Leipzig",
        "desc": "Elektro Hoffmann Leipzig — Elektriker, Installation, Smart Home, Notdienst",
        "niche_hint": "handwerk",
        "services": ["Elektroinstallation", "Smart Home", "Störungssuche", "Notdienst"],
    },
    {
        "id": "photographer",
        "name": "Studio Licht",
        "city": "Düsseldorf",
        "desc": "Studio Licht Düsseldorf — Fotograf, Portraits, Hochzeit, Business-Fotos",
        "niche_hint": "photography",
        "services": ["Portraits", "Hochzeitsfotografie", "Business-Portraits", "Studio"],
    },
    {
        "id": "fitness",
        "name": "FitLab Studio",
        "city": "Dortmund",
        "desc": "FitLab Studio Dortmund — Fitnessstudio, Personal Training, Kurse",
        "niche_hint": "fitness",
        "services": ["Personal Training", "Gruppenskurse", "Probe-Training", "Ernährungscoaching"],
    },
    {
        "id": "realestate",
        "name": "Immobilien Atlas",
        "city": "Hannover",
        "desc": "Immobilien Atlas Hannover — Immobilienmakler, Verkauf, Vermietung, Bewertung",
        "niche_hint": "realestate",
        "services": ["Immobilienbewertung", "Verkauf", "Vermietung", "Besichtigung"],
    },
]

_WEAK_CTA = {
    "mehr erfahren",
    "learn more",
    "kontakt aufnehmen",
    "contact us",
    "click here",
}

_BANNED = (
    "partner vor ort",
    "helfen ihrem unternehmen",
    "virtus core",
    "genesis.exe",
    "lorem ipsum",
    "coming soon",
    "sample text",
)


def _build(case: dict):
    analysis = analyze(case["desc"], niche_hint=case.get("niche_hint"))
    contacts = {
        "business_name": case["name"],
        "city": case["city"],
        "phone": "+49 40 1234567",
        "email": f"kontakt@{case['id']}.example.de",
        "services_list": case["services"],
        "niche": case.get("niche_hint") or analysis.niche,
        "package_id": "basic",
        "market_code": "DE",
    }
    out, gate = run_composers(
        analysis,
        contacts=contacts,
        package_id="basic",
        scenario_id=analysis.niche,
    )
    ctx = context_from_contacts(contacts, niche=out.niche, business_name=case["name"])
    design = compose_design_meta(ctx)
    layout = compose_layout_profile(ctx)
    return out, gate, design, layout, preferred_layout_ids(ctx)


def test_acceptance_10_niches_commercial_ready():
    rows = []
    headlines: set[str] = set()
    ctas: set[str] = set()
    layout_ids: set[str] = set()
    primaries: set[str] = set()
    tones: set[str] = set()

    for case in _CASES:
        out, gate, design, layout, pool = _build(case)
        blob = " ".join(
            [
                out.headline or "",
                out.subtitle or "",
                out.about_text or "",
                out.cta_label or "",
                " ".join(out.services or []),
            ]
        ).lower()

        assert gate.hard_passed, f"{case['id']} Hard Gate FAIL: {gate.failures}"
        assert gate.brand_leak == "PASS", f"{case['id']} brand leak"
        assert not any(b in blob for b in _BANNED), f"{case['id']} banned copy: {blob[:120]}"
        assert out.headline and " — " in out.headline, f"{case['id']} weak hero"
        assert (out.cta_label or "").lower() not in _WEAK_CTA, f"{case['id']} weak CTA: {out.cta_label}"
        assert len(out.services or []) >= 2, f"{case['id']} too few services"
        # Questionnaire services must appear
        overlap = sum(1 for s in case["services"] if s in (out.services or []))
        assert overlap >= 2, f"{case['id']} services not from questionnaire: {out.services}"

        # Niche personality: photographer must not look like fashion boutique
        if case["id"] == "photographer":
            assert out.niche == "photography", out.niche
            assert "kollektion" not in (out.cta_label or "").lower()
            assert "mode mit charakter" not in (out.headline or "").lower()
        if case["id"] == "accountant":
            assert out.niche == "accounting", out.niche
            assert "migrations" not in (out.headline or "").lower()
        if case["id"] == "fitness":
            assert out.niche == "fitness", out.niche
            assert (out.headline or "").lower().count(case["name"].lower()) <= 1

        headlines.add(out.headline.strip().lower())
        ctas.add((out.cta_label or "").strip().lower())
        layout_ids.add(getattr(layout, "id", "") or "")
        if design.get("primary"):
            primaries.add(str(design["primary"]))
        if design.get("emotional_tone"):
            tones.add(str(design["emotional_tone"]))

        rows.append(
            {
                "id": case["id"],
                "niche": out.niche,
                "headline": out.headline,
                "cta": out.cta_label,
                "layout": getattr(layout, "id", None),
                "tone": design.get("emotional_tone"),
                "primary": design.get("primary"),
                "score": gate.ai_score.overall,
                "hard": gate.hard_passed,
                "score_ok": gate.score_passed,
            }
        )

    # Cross-niche diversity — not one template with renamed company
    assert len(headlines) == len(_CASES), f"duplicate heroes: {sorted(headlines)}"
    assert len(ctas) >= 5, f"CTA diversity too low: {ctas}"
    assert len(layout_ids) >= 3, f"layout diversity too low: {layout_ids}"
    assert len(primaries) >= 4 or len(tones) >= 4, (
        f"design diversity too low primaries={primaries} tones={tones}"
    )

    # Print summary for CEO (pytest -s) — ASCII-safe for Windows consoles
    print("\n=== Commercial acceptance 10 niches ===")
    for r in rows:
        hero = (r["headline"] or "").encode("ascii", "replace").decode("ascii")
        cta = (r["cta"] or "").encode("ascii", "replace").decode("ascii")
        print(
            f"{r['id']:12} niche={r['niche']:12} layout={r['layout']} "
            f"score={r['score']} CTA={cta!r} hard={r['hard']} score_ok={r['score_ok']}"
        )
        print(f"             hero={hero!r}")

    hard_fail = [r for r in rows if not r["hard"]]
    assert not hard_fail, f"Hard Gate failures: {hard_fail}"
    score_fail = [r for r in rows if not r["score_ok"]]
    assert not score_fail, f"AI Score failures after Hard Gate: {score_fail}"
