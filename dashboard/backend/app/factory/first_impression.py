"""First Impression Generation — not Hero Generation.

Factory does not generate a page hero block.
It generates the client's first 3 seconds:

  Client story (problem before click)
    → Emotion
    → Trust
    → Offer
    → CTA

Composition + photo/video + type + light + space + headline + motion + button + atmosphere
are one impression — not separate features.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.factory.analyzer import AnalysisResult
from app.factory.dream_brief import DreamBrief, dream_brief_from_contacts


# Owner RC1 — client story beats company slogan.
PREMIUM_FIRST_IMPRESSIONS: dict[str, dict[str, str]] = {
    "dachreinigung": {
        "problem_before": (
            "Nach dem Winter liegt Moos auf dem Dach. "
            "Sie öffnen den Browser und fürchten schon die Sanierungskosten."
        ),
        "story": (
            "Nach dem Winter ist das Dach voller Moos — "
            "und Sie fürchten, die Sanierung kostet Tausende."
        ),
        "emotion": "Erleichterung statt Panik vor der Rechnung.",
        "trust": "Versichert, dokumentiert, Festpreis vor Ort.",
        "offer": (
            "Wir kommen, reinigen, dokumentieren das Ergebnis "
            "und verlängern die Lebensdauer Ihres Dachs."
        ),
        "idea": "Nach dem Regen sieht das Dach wieder neu aus.",
    },
    "psychology": {
        "problem_before": (
            "Sie tragen etwas mit sich, das schwer bleibt — "
            "und wissen nicht, ob ein Gespräch überhaupt hilft."
        ),
        "story": (
            "Manchmal reicht ein Gespräch, "
            "um wieder Boden unter den Füßen zu spüren."
        ),
        "emotion": "Wieder Boden unter den Füßen.",
        "trust": "Vertraulich. Klar. In Ihrem Tempo.",
        "offer": "Ein geschützter Raum für das erste Gespräch — online oder vor Ort.",
        "idea": "Ein Ort, an dem es ruhiger wird.",
    },
    "law": {
        "problem_before": (
            "Die Lage wird unübersichtlich. "
            "Sie brauchen keinen Theatersaal — Sie brauchen einen Weg."
        ),
        "story": (
            "Wenn die Lage schwierig wird, zählt, "
            "dass jemand den Weg zur Lösung schon kennt."
        ),
        "emotion": "Kontrolle kehrt zurück.",
        "trust": "Ruhig. Präzise. Vertraulich.",
        "offer": "Erste Orientierung in der Erstberatung — ohne Nebel.",
        "idea": "Stille. Ordnung. Kontrolle.",
    },
    "restaurant": {
        "problem_before": (
            "Sie wollen nicht nur essen — "
            "Sie wollen den Abend schon spüren, bevor die Karte kommt."
        ),
        "story": (
            "Hier beginnt der Abend nicht mit der Speisekarte, "
            "sondern mit dem Gefühl, schon in Italien zu sein."
        ),
        "emotion": "Ankommen — wie im Hof.",
        "trust": "Frische Zutaten. Allergene klar. Reservierung mit Bestätigung.",
        "offer": "Ein Tisch, der sich anfühlt wie bei Freunden.",
        "idea": "Ein Abend im italienischen Hof.",
    },
    "beauty": {
        "problem_before": (
            "Sie wollen keinen Wartesaal und keinen Trend-Druck — "
            "nur Zeit, die wirklich Ihnen gehört."
        ),
        "story": "Zeit, die nur Ihnen gehört.",
        "emotion": "Ruhe vor dem Spiegel.",
        "trust": "Beratung vor dem Schnitt. Ehrliche Preise.",
        "offer": "Ein Atelier-Ritual — kein Salon-Durchlauf.",
        "idea": "Ein Ritual der Schönheit — kein Salon.",
    },
    "dental": {
        "problem_before": (
            "Zahnarztangst und unklare Kosten — "
            "Sie wollen wissen, was passiert, bevor etwas bohrt."
        ),
        "story": "Zähne ohne Angst — und Kosten, die Sie vorher kennen.",
        "emotion": "Ruhe im Behandlungsstuhl.",
        "trust": "Aufklärung vor Behandlung. Moderne Praxis.",
        "offer": "Prophylaxe bis Implantat — klar erklärt.",
        "idea": "Präzision, die Ruhe gibt.",
    },
    "handwerk": {
        "problem_before": (
            "Kleinreparatur, Montage, tropfender Hahn — Sie brauchen jemanden, "
            "der kommt, festpreist und nicht drei Wochen später."
        ),
        "story": "Meister vor Ort — stundenweise, klar kalkuliert.",
        "emotion": "Entlastung: jemand übernimmt den Haushalt-Job.",
        "trust": "Festpreis nach Aufmaß. Saubere Übergabe. WhatsApp-Termin.",
        "offer": "Montage, Reparatur, IKEA-Aufbau, Streichen — ab einer Stunde.",
        "idea": "Der Meister, der wirklich kommt.",
    },
    "auto": {
        "problem_before": (
            "Das Auto streikt — und Sie fürchten die Werkstatt-Rechnung ohne Diagnose."
        ),
        "story": "Erst Diagnose, dann Preis — ohne Verkaufsdruck.",
        "emotion": "Klarheit statt Werkstatt-Theater.",
        "trust": "Schriftliche Diagnose. Garantie auf Arbeit.",
        "offer": "Inspektion, Reifen, Reparatur — ehrlich kalkuliert.",
        "idea": "Technik ohne Theater.",
    },
    "fitness": {
        "problem_before": (
            "Sie wollen starten — ohne monatelanges Abo und ohne peinliche Probetrainings-Show."
        ),
        "story": "Training, das zu Ihrem Alltag passt — nicht umgekehrt.",
        "emotion": "Energie ohne Druck.",
        "trust": "Coaches vor Ort. Klare Mitgliedschaft.",
        "offer": "Probetraining ohne Vertragsfalle.",
        "idea": "Form mit Haltung.",
    },
    "realestate": {
        "problem_before": (
            "Verkauf oder Miete — Sie wollen nicht im Exposé-Nebel untergehen."
        ),
        "story": "Immobilie verkaufen — mit klarer Strategie, nicht mit Hoffnung.",
        "emotion": "Überblick statt Marktdruck.",
        "trust": "Lokale Marktkenntnis. Transparente Provision.",
        "offer": "Bewertung, Exposé, Begleitung bis Notar.",
        "idea": "Wohnraum mit Klarheit.",
    },
    "zaunbau": {
        "problem_before": (
            "Der Zaun ist kaputt oder fehlt — Sie wollen Sichtschutz, "
            "ohne monatelanges Warten und ohne Pfusch-Montage."
        ),
        "story": "Zaun und Tor — Aufmaß, Festpreis, saubere Montage.",
        "emotion": "Grenze mit Ruhe.",
        "trust": "Deutsche Qualität. Aufmaß vor Ort.",
        "offer": "Sichtschutz, Doppelstab, Tor — montiert und dokumentiert.",
        "idea": "Grenze, die hält.",
    },
    "gartenpflege": {
        "problem_before": (
            "Der Garten wächst Ihnen über den Kopf — "
            "Sie brauchen Termine, die kommen, und einen Plan fürs Jahr."
        ),
        "story": "Garten in Ordnung — mit festen Terminen, nicht mit Versprechen.",
        "emotion": "Grün ohne Stress.",
        "trust": "Zuverlässige Termine. Klarer Jahresplan.",
        "offer": "Rasen, Hecke, Beete — saisonal betreut.",
        "idea": "Ordnung im Grün.",
    },
}


@dataclass(frozen=True)
class FirstImpression:
    """One commercial beat — Story → Emotion → Trust → Offer → CTA."""

    niche_id: str
    problem_before: str
    story: str
    emotion: str
    trust: str
    offer: str
    idea: str
    source: str
    stage_name: str = "First Impression Generation"

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["arc"] = ["story", "emotion", "trust", "offer", "cta"]
        d["rule"] = (
            "Not a slogan. Not a section list. "
            "What does the client feel 10 seconds before they open this site?"
        )
        d["three_second_test"] = THREE_SECOND_TEST
        return d


THREE_SECOND_TEST: dict[str, Any] = {
    "name": "3-SECOND TEST",
    "instructions": (
        "Open the site. Do not read the text. After 3 seconds answer:"
    ),
    "questions": [
        "What does the company do?",
        "Can I trust it?",
        "Does it look cheap or expensive?",
        "Do I want to look further?",
        "Does it look like a template?",
    ],
    "rule": "If any answer is negative or unclear → REBUILD.",
}


class FirstImpressionError(RuntimeError):
    """Premium without a client story fails First Impression Generation."""


def resolve_first_impression(
    *,
    niche_id: str,
    contacts: dict | None = None,
    dream: DreamBrief | None = None,
) -> FirstImpression:
    niche = (niche_id or "").strip().lower() or "generic"
    d = dream or dream_brief_from_contacts(contacts)
    pack = PREMIUM_FIRST_IMPRESSIONS.get(niche) or {}
    c = contacts if isinstance(contacts, dict) else {}
    dream_d = c.get("dream_brief") if isinstance(c.get("dream_brief"), dict) else {}

    story = (
        str(dream_d.get("client_story") or c.get("client_story") or "").strip()
        or str(getattr(d, "client_story", "") or "").strip()
        or str(pack.get("story") or "").strip()
    )
    problem = (
        str(dream_d.get("problem_before") or c.get("problem_before") or "").strip()
        or str(getattr(d, "problem_before", "") or "").strip()
        or str(pack.get("problem_before") or "").strip()
    )
    source = "premium_pack" if pack and story == pack.get("story") else "dream_brief"
    if not story and pack:
        story = str(pack.get("story") or "")
        source = "premium_pack"

    return FirstImpression(
        niche_id=niche,
        problem_before=problem,
        story=story,
        emotion=str(pack.get("emotion") or d.brand_feeling or ""),
        trust=str(pack.get("trust") or d.why_choose_us or ""),
        offer=str(pack.get("offer") or d.main_promise or ""),
        idea=str(
            pack.get("idea")
            or getattr(d, "commercial_idea", "")
            or d.main_promise
            or ""
        ),
        source=source if story else "missing",
    )


def assert_first_impression(
    fi: FirstImpression,
    *,
    package_id: str = "business",
    hard: bool = True,
) -> dict[str, Any]:
    pid = (package_id or "").strip().lower()
    ok = bool(fi.story) and len(fi.story.strip()) >= 16
    # Client story must not be a bare service list
    low = fi.story.lower()
    generic = any(
        g in low
        for g in (
            "wir waschen",
            "wir bieten",
            "unsere leistungen",
            "willkommen bei",
            "professionelle leistungen",
        )
    )
    ok = ok and not generic
    report = {
        "gate": "FIRST_IMPRESSION",
        "stage": "First Impression Generation",
        "ok": ok,
        "story": fi.story,
        "problem_before": fi.problem_before,
        "package_id": pid,
        "source": fi.source,
        "three_second_test": THREE_SECOND_TEST,
        "question": "What problem does the client feel 10 seconds before opening this site?",
    }
    if hard and pid == "premium" and not ok:
        raise FirstImpressionError(
            f"FIRST_IMPRESSION_FAIL: no client story — {fi.story!r}"
        )
    return report


def apply_first_impression_to_analysis(
    analysis: AnalysisResult,
    fi: FirstImpression,
) -> AnalysisResult:
    """Hero H1 = client story; lead = emotion + offer; trust rail = trust line.

    Commercial Hard Gate still requires a niche cue (name — story, niche word,
    or service). Pure emotion lines like «Zeit, die nur Ihnen gehört.» without
    that cue freeze client ZIP delivery — keep the story, prefix the brand.
    """
    from dataclasses import replace

    if not fi.story:
        return analysis
    story = fi.story.strip()
    name = (analysis.business_name or "").strip()
    headline = story
    if name and " — " not in story:
        headline = f"{name} — {story}"
    subtitle = fi.emotion
    if fi.offer:
        subtitle = f"{fi.emotion} {fi.offer}".strip() if fi.emotion else fi.offer
    trust = list(analysis.trust_points or ())
    if fi.trust:
        trust = [fi.trust, *[t for t in trust if t != fi.trust]][:4]
    return replace(
        analysis,
        headline=headline,
        subtitle=subtitle[:320],
        trust_points=tuple(trust),
    )


def write_first_impression(
    product_dir: Path | str,
    fi: FirstImpression,
    report: dict | None = None,
) -> None:
    import json

    root = Path(product_dir)
    root.mkdir(parents=True, exist_ok=True)
    payload = fi.as_dict()
    if report:
        payload["gate_report"] = report
    (root / "first_impression.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def fi_hero_attrs(fi: FirstImpression | None) -> str:
    if fi is None:
        return 'data-stage="first-impression-generation"'
    return (
        'data-stage="first-impression-generation" '
        'data-first-impression="1" '
        f'data-fi-source="{fi.source}"'
    )


FIRST_IMPRESSION = "First Impression Generation"


__all__ = [
    "FIRST_IMPRESSION",
    "FirstImpression",
    "FirstImpressionError",
    "PREMIUM_FIRST_IMPRESSIONS",
    "THREE_SECOND_TEST",
    "apply_first_impression_to_analysis",
    "assert_first_impression",
    "fi_hero_attrs",
    "resolve_first_impression",
    "write_first_impression",
]
