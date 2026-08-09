"""Section rhythm — never two consecutive light treatments (Goal B)."""

from __future__ import annotations

import hashlib

from app.factory.design_dna.dna import Treatment

DEFAULT_SECTION_KEYS = (
    "stats",
    "services",
    "reputation",
    "mid_cta",
    "benefits",
    "trust",
    "process",
    "showcase",
    "gallery",
    "about",
    "faq",
    "reviews",
    "maps",
    "contact",
)

# Light family = reads as "white ladder" if repeated
_LIGHT = frozenset({"open_light", "tint"})

_TREAT_CYCLE: dict[str, tuple[Treatment, ...]] = {
    "scandinavian_calm": (
        "tint",
        "ink",
        "gradient",
        "glass",
        "photo_band",
        "tint",
        "illustration",
    ),
    "nature_therapy": (
        "photo_band",
        "tint",
        "ink",
        "gradient",
        "glass",
        "illustration",
        "ink",
    ),
    "luxury_studio": (
        "ink",
        "glass",
        "photo_band",
        "gradient",
        "ink",
        "glass",
        "tint",
    ),
    "editorial": (
        "ink",
        "photo_band",
        "gradient",
        "glass",
        "ink",
        "tint",
        "photo_band",
    ),
    "modern_clinical": (
        "tint",
        "glass",
        "ink",
        "gradient",
        "illustration",
        "ink",
        "glass",
    ),
    "organic_premium": (
        "illustration",
        "tint",
        "ink",
        "gradient",
        "glass",
        "photo_band",
        "ink",
    ),
}

_ALT_DARK: tuple[Treatment, ...] = ("ink", "gradient", "glass", "photo_band", "illustration")


def _seed_offset(seed: str, n: int) -> int:
    digest = hashlib.sha256(f"{seed}|{n}".encode("utf-8")).hexdigest()
    return int(digest[:6], 16)


def plan_section_rhythm(
    *,
    section_keys: tuple[str, ...] | list[str],
    style: str,
    package_id: str,
    seed: str,
) -> tuple[tuple[str, Treatment], ...]:
    """Assign visual treatments. Hard rule: never two light sections in a row."""
    keys = [k for k in section_keys if str(k).strip()]
    if not keys:
        keys = list(DEFAULT_SECTION_KEYS)

    cycle = _TREAT_CYCLE.get(style) or _TREAT_CYCLE["modern_clinical"]
    pid = (package_id or "basic").strip().lower()
    offset = _seed_offset(seed, len(keys)) % len(cycle)

    out: list[tuple[str, Treatment]] = []
    prev_light = False
    for i, key in enumerate(keys):
        treat: Treatment = cycle[(offset + i) % len(cycle)]
        if key in ("contact", "mid_cta", "late_cta") and pid != "basic":
            treat = "ink" if pid == "premium" else "gradient"
        if key in ("showcase", "gallery", "signature") and treat in _LIGHT:
            treat = "photo_band"
        if treat in _LIGHT and prev_light:
            treat = _ALT_DARK[(offset + i) % len(_ALT_DARK)]
        prev_light = treat in _LIGHT
        out.append((key, treat))
    return tuple(out)


def enforce_no_triple_light(treatments: list[Treatment]) -> list[Treatment]:
    """Post-pass: max one consecutive light treatment."""
    fixed: list[Treatment] = []
    prev_light = False
    i = 0
    for t in treatments:
        if t in _LIGHT and prev_light:
            t = _ALT_DARK[i % len(_ALT_DARK)]
        prev_light = t in _LIGHT
        fixed.append(t)
        i += 1
    return fixed


def validate_no_light_ladder(treatments: Sequence[Treatment] | list[Treatment]) -> list[str]:
    """Return failure codes if light ladder exists."""
    from typing import Sequence as Seq  # local — avoid circular

    fails: list[str] = []
    prev = False
    for t in treatments:
        light = t in _LIGHT
        if light and prev:
            fails.append("light_ladder")
            break
        prev = light
    return fails
