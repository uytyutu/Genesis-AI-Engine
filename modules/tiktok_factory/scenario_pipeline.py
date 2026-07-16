"""Educational scenario drafts from recurring patterns — no publish, no API calls."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from modules.tiktok_factory.gate import require_tiktok_enabled

MEDIA_PRINCIPLE_RU = (
    "Ролик только из повторяющейся полезной закономерности — не ради просмотров. "
    "Spider → частота проблемы → образовательный сценарий → человек утверждает → публикация → /order."
)

# Future Content Engine targets (one script → many channels). Horizon only.
SUPPORTED_CHANNELS = ("tiktok", "youtube_shorts", "linkedin", "blog")


@dataclass(frozen=True)
class ScenarioDraft:
    niche: str
    city: str
    pattern_issues: tuple[str, ...]
    hook_de: str
    body_beats_de: tuple[str, ...]
    cta_de: str
    order_path: str
    channels: tuple[str, ...]
    human_gate_required: bool = True
    doxx_forbidden: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def list_supported_channels() -> list[str]:
    return list(SUPPORTED_CHANNELS)


def build_educational_scenario(
    *,
    niche: str,
    city: str,
    pattern_issues: list[str],
    frequency_note: str = "",
) -> ScenarioDraft:
    """Build a draft script. Raises if TikTok kill switch is off."""
    require_tiktok_enabled()
    issues = tuple(str(i).strip() for i in pattern_issues if str(i).strip())[:3]
    if len(issues) < 1:
        raise ValueError("pattern_required")
    niche_l = (niche or "Handwerk").strip()
    city_l = (city or "Deutschland").strip()
    hook = (
        f"Warum {niche_l}-Betriebe in {city_l} Anrufe verlieren — "
        "oft ohne es zu merken."
    )
    beats = [
        "Typische Fehler (ohne Firmennamen): " + "; ".join(issues),
        "Ein verlorener Anruf kostet oft mehr als eine klare Landing Page.",
        "Nicht flicken — digitaler Neustart: moderne Landing Page in 5–7 Tagen.",
    ]
    if frequency_note.strip():
        beats.insert(1, f"Muster bestätigt: {frequency_note.strip()[:160]}")
    cta = "Link in Bio → Pakete & Bestellung (ohne Verpflichtung)."
    return ScenarioDraft(
        niche=niche_l,
        city=city_l,
        pattern_issues=issues,
        hook_de=hook,
        body_beats_de=tuple(beats),
        cta_de=cta,
        order_path="/order",
        channels=SUPPORTED_CHANNELS,
    )
