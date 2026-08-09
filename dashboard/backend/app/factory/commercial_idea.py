"""Commercial Reality — Who is the company? Then how does it look?

Law №3 + Commercial Reality Sprint:
Factory must invent a commercial IDEA readable in ~5 seconds.
If the idea is missing or generic → generation FAIL (not a soft warning).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.factory.analyzer import AnalysisResult
from app.factory.dream_brief import DreamBrief, dream_brief_from_contacts


# Owner RC1 exemplars — idea must be felt without reading body copy.
PREMIUM_COMMERCIAL_IDEAS: dict[str, dict[str, Any]] = {
    "dachreinigung": {
        "idea": "Nach dem Regen sieht das Dach wieder neu aus.",
        "idea_en": "After the rain, the roof looks new again.",
        "who": (
            "Deutsches Handwerk: Qualität, Sicherheit, Ordnung, "
            "Arbeit nach dem Regen, professionelle Technik, spürbare Zuverlässigkeit."
        ),
        "character": (
            "Qualität",
            "Sicherheit",
            "Akkuratesse",
            "Ordnung",
            "Nach dem Regen",
            "Profi-Technik",
            "Zuverlässigkeit",
        ),
        "metaphor": "Frischer Regen nach dem Sturm — nasse Ziegel, klarer Himmel",
        "hero_concept": "roof_after_rain",
        "emotion_3s": "Erleichterung und Stolz aufs eigene Haus",
    },
    "psychology": {
        "idea": "Ein Ort, an dem es ruhiger wird.",
        "idea_en": "A place where it gets quieter.",
        "who": (
            "Ruhige Praxis: Schutzraum, Tempo des Menschen, "
            "klare Honorare, keine Wellness-Floskeln."
        ),
        "character": ("Ruhe", "Schutz", "Klarheit", "Tempo des Menschen", "Vertrauen"),
        "metaphor": "Weiches Morgenlicht in einem stillen Raum",
        "hero_concept": "quiet_chamber",
        "emotion_3s": "Atem wird tiefer — hier darf man ankommen",
    },
    "restaurant": {
        "idea": "Ein Abend im italienischen Hof.",
        "idea_en": "An evening in an Italian courtyard.",
        "who": (
            "Familiäre Trattoria: Wärme, Abendlicht, ehrliche Küche, "
            "Tisch wie bei Freunden — kein Touristen-Menü."
        ),
        "character": ("Wärme", "Abendlicht", "Gastfreundschaft", "Produkt", "Erinnerung"),
        "metaphor": "Abendlicht über dem Hof — lange Tafel, leises Gläserklingen",
        "hero_concept": "italian_courtyard_evening",
        "emotion_3s": "Hunger auf den Abend — nicht auf eine Speisekarte-PDF",
    },
    "law": {
        "idea": "Stille. Ordnung. Kontrolle.",
        "idea_en": "Silence. Order. Control.",
        "who": (
            "Boutique-Kanzlei: präzise, vertraulich, ruhig-autoritär, "
            "klare Honorare, Orientierung vor Eskalation."
        ),
        "character": ("Stille", "Ordnung", "Kontrolle", "Präzision", "Vertraulichkeit"),
        "metaphor": "Ruhige Fassade, klares Licht, kein Theater",
        "hero_concept": "quiet_authority",
        "emotion_3s": "Hier behält jemand den Überblick",
    },
    "beauty": {
        "idea": "Ein Ritual der Schönheit — kein Salon.",
        "idea_en": "A beauty ritual — not a salon.",
        "who": (
            "Boutique-Atelier: Beratung vor dem Schnitt, ehrliche Produkte, "
            "Alltagstauglichkeit, kein Wartesaal-Gefühl."
        ),
        "character": ("Ritual", "Ruhe", "Präzision", "Alltag", "Haltung"),
        "metaphor": "Helles Atelierlicht — ruhige Hände, kein Neon-Salon",
        "hero_concept": "beauty_ritual",
        "emotion_3s": "Zeit für sich — nicht Warteschlange",
    },
    "handwerk": {
        "idea": "Der Meister, der wirklich kommt — stundenweise, klar kalkuliert.",
        "idea_en": "The craftsman who actually shows up — by the hour, clear price.",
        "who": (
            "Lokaler Handwerksbetrieb: Montage, Kleinreparatur, IKEA-Aufbau, "
            "Streichen, Bohren — Festpreis nach Aufmaß, saubere Übergabe."
        ),
        "character": (
            "Zuverlässigkeit",
            "Festpreis",
            "Sauberkeit",
            "Tempo",
            "Werkzeug",
            "Vor Ort",
        ),
        "metaphor": "Meister auf der Leiter — Bohrmaschine, fertige Küche, sauberer Boden",
        "hero_concept": "meister_on_site",
        "emotion_3s": "Endlich erledigt — ohne Baustellen-Chaos",
    },
}

_GENERIC_FAIL = (
    "klar. vertrauenswürdig",
    "qualität ohne show",
    "ihre lokale",
    "willkommen bei",
    "professionelle leistungen",
    "wir sind für sie da",
)


@dataclass(frozen=True)
class CommercialIdea:
    niche_id: str
    idea: str
    who: str
    character: tuple[str, ...]
    metaphor: str
    hero_concept: str
    emotion_3s: str
    source: str  # dream_brief | premium_pack | fabricated

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["character"] = list(self.character)
        d["rule"] = (
            "If the idea is not readable in 5 seconds without body copy → FAIL. "
            "Who-is-company comes before how-it-looks."
        )
        return d


class CommercialIdeaError(RuntimeError):
    """Raised when Premium generation has no readable commercial idea."""


def resolve_commercial_idea(
    *,
    niche_id: str,
    contacts: dict | None = None,
    dream: DreamBrief | None = None,
) -> CommercialIdea:
    niche = (niche_id or "").strip().lower() or "generic"
    d = dream or dream_brief_from_contacts(contacts)
    pack = PREMIUM_COMMERCIAL_IDEAS.get(niche) or {}

    idea = (
        str(getattr(d, "commercial_idea", "") or "").strip()
        or str((contacts or {}).get("commercial_idea") or "").strip()
        or (str(d.main_promise).strip() if d.main_promise else "")
        or str(pack.get("idea") or "").strip()
    )
    who = (
        str(getattr(d, "who_is_company", "") or "").strip()
        or str((contacts or {}).get("who_is_company") or "").strip()
        or (str(d.brand_feeling).strip() if d.brand_feeling else "")
        or str(pack.get("who") or "").strip()
    )
    character = tuple(pack.get("character") or ())
    if d.why_choose_us:
        who = who or d.why_choose_us
    source = "premium_pack" if pack and idea == pack.get("idea") else "dream_brief"
    if not idea and pack:
        idea = str(pack["idea"])
        source = "premium_pack"
    return CommercialIdea(
        niche_id=niche,
        idea=idea,
        who=who or "Eine echte lokale Marke mit Haltung.",
        character=character,
        metaphor=str(pack.get("metaphor") or d.brand_feeling or ""),
        hero_concept=str(pack.get("hero_concept") or ""),
        emotion_3s=str(pack.get("emotion_3s") or ""),
        source=source if idea else "missing",
    )


def idea_readable_in_five_seconds(idea: str) -> bool:
    text = (idea or "").strip()
    if len(text) < 12 or len(text) > 120:
        return False
    low = text.lower()
    if any(g in low for g in _GENERIC_FAIL):
        return False
    # Must feel like a sentence or punchy triad — not a service list
    if low.count(",") >= 5:
        return False
    return True


def assert_commercial_idea(
    idea: CommercialIdea,
    *,
    package_id: str = "business",
    hard: bool = True,
) -> dict[str, Any]:
    """Premium FAIL if idea cannot be felt in ~5 seconds."""
    pid = (package_id or "").strip().lower()
    ok = bool(idea.idea) and idea_readable_in_five_seconds(idea.idea)
    report = {
        "gate": "COMMERCIAL_IDEA",
        "ok": ok,
        "idea": idea.idea,
        "who": idea.who,
        "package_id": pid,
        "source": idea.source,
        "question": "Is the commercial idea readable in 5 seconds without body copy?",
    }
    if hard and pid == "premium" and not ok:
        raise CommercialIdeaError(
            f"COMMERCIAL_IDEA_FAIL: Premium idea missing or generic — {idea.idea!r}"
        )
    return report


def apply_commercial_idea_to_analysis(
    analysis: AnalysisResult,
    idea: CommercialIdea,
) -> AnalysisResult:
    """Hero carries the IDEA; subtitle carries who-the-company-is."""
    from dataclasses import replace

    if not idea.idea:
        return analysis
    # H1 = commercial idea (not "{Brand} — slogan")
    headline = idea.idea
    # Lead = who / character — readable without services list
    subtitle = idea.who
    if idea.character and len(subtitle) < 40:
        subtitle = f"{subtitle} · " + " · ".join(idea.character[:4])
    return replace(
        analysis,
        headline=headline,
        subtitle=subtitle[:280],
    )


def write_commercial_idea(product_dir, idea: CommercialIdea, report: dict | None = None) -> None:
    from pathlib import Path
    import json

    root = Path(product_dir)
    root.mkdir(parents=True, exist_ok=True)
    payload = idea.as_dict()
    if report:
        payload["gate_report"] = report
    (root / "commercial_idea.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "CommercialIdea",
    "CommercialIdeaError",
    "PREMIUM_COMMERCIAL_IDEAS",
    "apply_commercial_idea_to_analysis",
    "assert_commercial_idea",
    "idea_readable_in_five_seconds",
    "resolve_commercial_idea",
    "write_commercial_idea",
]
