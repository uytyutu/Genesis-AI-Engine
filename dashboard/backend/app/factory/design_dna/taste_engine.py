"""AI Taste Engine — Virtus Core Studio Era.

Not rigid checklists ("≤2 white sections"). Holistic judgment of the
visual whole: beauty, rhythm, emotion, brand, trust, modernity,
visual value, uniqueness.

A fully white site can be magnificent if composition earns it.
A colorful site can fail if it feels like a constructor.

HTML is evidence. Taste decides. Owner still owns PASS.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

TasteAxis = Literal[
    "beauty",
    "rhythm",
    "emotion",
    "brand",
    "trust",
    "modernity",
    "visual_value",
    "uniqueness",
]

TASTE_AXES: tuple[TasteAxis, ...] = (
    "beauty",
    "rhythm",
    "emotion",
    "brand",
    "trust",
    "modernity",
    "visual_value",
    "uniqueness",
)


@dataclass(frozen=True)
class TasteAxisScore:
    axis: TasteAxis
    score: float  # 0..100
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TasteVerdict:
    """Holistic taste reading — never auto visual PASS."""

    overall: float  # 0..100
    axes: list[TasteAxisScore] = field(default_factory=list)
    verdict: str = "PENDING_OWNER"  # STRONG | PROMISING | WEAK | FAIL_TASTE
    rebuild: bool = False
    reasons: list[str] = field(default_factory=list)
    philosophy: str = (
        "Taste judges the whole impression — not isolated CSS rules."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "overall": round(self.overall, 2),
            "axes": [a.as_dict() for a in self.axes],
            "verdict": self.verdict,
            "rebuild": self.rebuild,
            "reasons": list(self.reasons),
            "philosophy": self.philosophy,
            "owner_still_decides_pass": True,
        }


def _clamp(x: float) -> float:
    return max(0.0, min(100.0, x))


def evaluate_taste(
    *,
    html: str = "",
    composition_id: str = "",
    hero_layout: str = "",
    scene_sequence: list[str] | None = None,
    brand_feeling: str = "",
    why_hero_exists: str = "",
    studio_approach: str = "",
    package_id: str = "business",
    predictable_funnel: bool = False,
    generation_status: str = "OK_TO_BUILD",
    fingerprint: str = "",
    prior_best_overall: float | None = None,
) -> TasteVerdict:
    """Score the *whole* experience from available signals.

    Structural proxies only — eyes still decide. Never mints PASS.
    """
    html_l = (html or "").lower()
    scenes = scene_sequence or []
    pid = (package_id or "business").strip().lower()
    axes: list[TasteAxisScore] = []
    reasons: list[str] = []

    # --- Rhythm: scene arc vs constructor ladder ---
    rhythm = 72.0
    if predictable_funnel or generation_status == "FAIL_TEMPLATE":
        rhythm = 18.0
        reasons.append("Constructor ladder / FAIL_TEMPLATE kills rhythm")
    elif scenes:
        # Diversity of scene roles = breathing page
        uniq = len(set(scenes))
        rhythm = _clamp(40 + uniq * 10)
        if scenes[:2] == ["scene", "experience"]:
            rhythm -= 12
            reasons.append("Offer-heavy early — weak emotional lead")
        if "story" in scenes[:4] or "emotion" in scenes[:4]:
            rhythm += 8
    axes.append(TasteAxisScore("rhythm", _clamp(rhythm), "scene arc vs ladder"))

    # --- Emotion: why hero + brand feeling present ---
    emotion = 55.0
    if why_hero_exists and len(why_hero_exists) > 40:
        emotion += 20
    else:
        emotion -= 15
        reasons.append("Hero chosen without a clear *why*")
    if brand_feeling:
        emotion += 10
    if any(w in (brand_feeling or "").lower() for w in ("calm", "luxury", "warm", "prestige", "alive")):
        emotion += 5
    axes.append(TasteAxisScore("emotion", _clamp(emotion), "feeling + why-hero"))

    # --- Brand: approach + composition identity ---
    brand = 58.0
    if studio_approach:
        brand += 15
    if composition_id and composition_id not in ("cards_first", "corporate"):
        brand += 10
    elif composition_id in ("cards_first",):
        brand -= 20
        reasons.append("cards_first reads as template brand")
    axes.append(TasteAxisScore("brand", _clamp(brand), "approach + composition identity"))

    # --- Beauty / visual value: atmosphere & hero depth in HTML ---
    beauty = 50.0
    visual_value = 50.0
    if "dna-atm" in html_l or "dna-atm__" in html_l:
        beauty += 18
        visual_value += 14
    if "hero-layout-d" in html_l or 'data-hero-layout="d"' in html_l:
        beauty += 8
        visual_value += 10
    if "hero-luxury" in html_l or "vie-cinematic" in html_l:
        beauty += 6
        visual_value += 6
    # White slabs alone are NOT a fail — only empty decorative zones
    white_hits = len(re.findall(r"background:\s*#fff\b|background:\s*#ffffff\b", html_l))
    empty_zone = "placeholder" in html_l or "via.placeholder" in html_l
    if empty_zone:
        beauty -= 35
        visual_value -= 35
        reasons.append("Placeholder / empty media destroys beauty")
    elif white_hits > 8 and "dna-atm" not in html_l:
        beauty -= 8  # soft signal only
        reasons.append("Many flat whites without atmosphere — watch composition")
    axes.append(TasteAxisScore("beauty", _clamp(beauty), "atmosphere + media integrity"))
    axes.append(TasteAxisScore("visual_value", _clamp(visual_value), "worth looking at"))

    # --- Trust ---
    trust = 55.0
    if "trust" in html_l or "schweigepflicht" in html_l or "impressum" in html_l:
        trust += 15
    if "fake" in html_l and "counter" in html_l:
        trust -= 25
    axes.append(TasteAxisScore("trust", _clamp(trust), "proof craft"))

    # --- Modernity ---
    modernity = 60.0
    if studio_approach in ("editorial", "luxury", "tech_saas", "boutique", "scandinavian"):
        modernity += 12
    if pid == "premium":
        modernity += 5
    if predictable_funnel:
        modernity -= 30
    axes.append(TasteAxisScore("modernity", _clamp(modernity), "2026 studio language"))

    # --- Uniqueness ---
    uniqueness = 55.0
    if fingerprint:
        uniqueness += 10
    if composition_id in (
        "chamber",
        "whisper",
        "overture",
        "solstice",
        "atelier_night",
        "breath",
        "magazine",
        "cinematic",
    ):
        uniqueness += 12
    if composition_id in ("cards_first", "corporate"):
        uniqueness -= 18
    axes.append(TasteAxisScore("uniqueness", _clamp(uniqueness), "not another clone"))

    overall = sum(a.score for a in axes) / max(1, len(axes))

    # Law #1 soft check: not worse than prior best (when known)
    if prior_best_overall is not None and overall + 2.0 < prior_best_overall:
        reasons.append(
            f"Law #1 risk: taste {overall:.0f} < prior best {prior_best_overall:.0f}"
        )
        overall = _clamp(overall - 5)

    rebuild = False
    if predictable_funnel or generation_status == "FAIL_TEMPLATE":
        verdict = "FAIL_TASTE"
        rebuild = True
    elif overall >= 78:
        verdict = "STRONG"
    elif overall >= 62:
        verdict = "PROMISING"
    elif overall >= 45:
        verdict = "WEAK"
        rebuild = pid == "premium"
        if rebuild:
            reasons.append("Premium below taste bar — REBUILD")
    else:
        verdict = "FAIL_TASTE"
        rebuild = True
        reasons.append("Holistic taste too low — REBUILD")

    return TasteVerdict(
        overall=_clamp(overall),
        axes=axes,
        verdict=verdict,
        rebuild=rebuild,
        reasons=reasons,
    )
