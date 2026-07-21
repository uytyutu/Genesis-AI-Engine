"""R3.2 — Section-Aware Media Gate (no LLM).

Goal: do not publish illogical media — not «generate better».

Pipeline: niche + section → allowed/denied categories → media tags → PASS/FAIL.
On FAIL: caller swaps candidate or marks deliverable not publish-ready.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

Section = Literal["hero", "gallery", "services", "about", "contact"]

SECTIONS: tuple[Section, ...] = ("hero", "gallery", "services", "about", "contact")

# What a buyer expects to see in each block (union of safe roles).
SECTION_EXPECT: dict[Section, frozenset[str]] = {
    "hero": frozenset(
        {
            "product",
            "specialist",
            "interior",
            "result",
            "facade",
            "salon",
            "client",
            "laptop",
            "repair",
            "garden",
            "plants",
            "landscape",
            "auto",
            "workshop",
            "dental",
            "clinic",
            "law",
            "office",
            "craft",
            "energy",
            "restaurant",
            "food",
            "team",
        }
    ),
    "gallery": frozenset(
        {"work", "interior", "team", "result", "product", "process", "craft", "gallery"}
    ),
    "services": frozenset(
        {"process", "service", "equipment", "repair", "product", "work", "tools"}
    ),
    "about": frozenset(
        {"team", "owner", "office", "interior", "specialist", "salon", "clinic"}
    ),
    "contact": frozenset(
        {"facade", "map", "entrance", "reception", "office", "exterior", "interior"}
    ),
}

# Slot name in Hero Pack → section role for gate checks.
SLOT_TO_SECTION: dict[str, Section] = {
    "hero": "hero",
    "hero_1": "hero",
    "hero_2": "hero",
    "hero_3": "hero",
    "gallery": "gallery",
    "banner": "gallery",
    "showcase": "gallery",
    "services": "services",
    "cta": "services",
    "calculator": "services",
    "background_1": "about",
    "background_2": "about",
    "footer": "contact",
}


@dataclass(frozen=True)
class NicheMediaRule:
    allow: frozenset[str]
    deny: frozenset[str]


# Niche ownership defaults — files under showcases/{niche}/ inherit these tags.
NICHE_DEFAULT_TAGS: dict[str, frozenset[str]] = {
    "beauty": frozenset({"salon", "specialist", "interior", "client", "cosmetics", "product"}),
    "computer": frozenset({"laptop", "repair", "specialist", "equipment", "process", "tools"}),
    "green": frozenset({"garden", "plants", "landscape", "result", "exterior", "work"}),
    "dental": frozenset({"dental", "clinic", "specialist", "interior", "result", "equipment"}),
    "auto": frozenset({"auto", "workshop", "repair", "process", "equipment", "tools"}),
    "law": frozenset({"law", "office", "specialist", "interior", "team"}),
    "handwerk": frozenset({"craft", "work", "process", "tools", "result", "workshop"}),
    "energy": frozenset({"energy", "exterior", "result", "product", "work"}),
    "appliance": frozenset({"repair", "equipment", "process", "tools", "product"}),
    "restaurant": frozenset({"restaurant", "food", "interior", "product", "client"}),
    # Generic pack is retail / boutique / florist family — must not pass niche-specific heroes.
    "generic": frozenset({"retail", "boutique", "florist", "restaurant", "interior"}),
}

NICHE_RULES: dict[str, NicheMediaRule] = {
    "beauty": NicheMediaRule(
        allow=frozenset({"specialist", "salon", "client", "interior", "result", "cosmetics", "product"}),
        deny=frozenset(
            {
                "restaurant",
                "food",
                "florist",
                "retail",
                "boutique",
                "industry",
                "industrial",
                "auto",
                "workshop",
                "dental",
                "laptop",
                "computer",
                "garden",
                "landscape",
            }
        ),
    ),
    "computer": NicheMediaRule(
        allow=frozenset({"laptop", "specialist", "repair", "equipment", "process", "tools"}),
        deny=frozenset(
            {
                "florist",
                "flowers",
                "plants",
                "cafe",
                "restaurant",
                "food",
                "retail",
                "boutique",
                "dental",
                "salon",
                "cosmetics",
                "garden",
                "auto",
            }
        ),
    ),
    "green": NicheMediaRule(
        allow=frozenset({"garden", "plants", "landscape", "result", "exterior", "work"}),
        deny=frozenset(
            {
                "cosmetics",
                "salon",
                "restaurant",
                "food",
                "cafe",
                "dental",
                "laptop",
                "auto",
                "retail",
                "boutique",
            }
        ),
    ),
    "dental": NicheMediaRule(
        allow=frozenset({"dental", "clinic", "specialist", "interior", "result", "equipment", "team"}),
        deny=frozenset({"restaurant", "florist", "retail", "boutique", "auto", "laptop", "garden"}),
    ),
    "auto": NicheMediaRule(
        allow=frozenset({"auto", "workshop", "repair", "process", "equipment", "tools", "result"}),
        deny=frozenset({"salon", "florist", "restaurant", "dental", "law", "laptop", "garden"}),
    ),
    "law": NicheMediaRule(
        allow=frozenset({"law", "office", "specialist", "interior", "team"}),
        deny=frozenset({"auto", "workshop", "salon", "florist", "restaurant", "dental", "laptop", "garden"}),
    ),
    "handwerk": NicheMediaRule(
        allow=frozenset({"craft", "work", "process", "tools", "result", "workshop", "interior"}),
        deny=frozenset({"salon", "florist", "restaurant", "dental", "law", "laptop"}),
    ),
    "energy": NicheMediaRule(
        allow=frozenset({"energy", "exterior", "result", "product", "work"}),
        deny=frozenset({"salon", "florist", "restaurant", "dental", "laptop", "cosmetics"}),
    ),
    "restaurant": NicheMediaRule(
        allow=frozenset({"restaurant", "food", "interior", "product", "client", "team"}),
        deny=frozenset({"dental", "laptop", "auto", "workshop", "salon", "law", "garden"}),
    ),
    "appliance": NicheMediaRule(
        allow=frozenset({"repair", "equipment", "process", "tools", "product"}),
        deny=frozenset({"salon", "florist", "restaurant", "dental", "garden", "law"}),
    ),
    "generic": NicheMediaRule(
        allow=frozenset({"retail", "boutique", "interior", "product", "office", "team"}),
        deny=frozenset(),  # soft — generic site may use generic pack
    ),
}

# Explicit path overrides (relative to showcases/) for known mis-curated / ambiguous assets.
_TAG_OVERRIDES: dict[str, frozenset[str]] = {
    "generic/preview.jpg": frozenset({"retail", "boutique", "restaurant", "interior"}),
}


@dataclass(frozen=True)
class MediaGateCheck:
    section: str
    path: str
    ok: bool
    tags: tuple[str, ...] = ()
    detail: str = ""


@dataclass
class MediaGateResult:
    passed: bool
    checks: list[MediaGateCheck] = field(default_factory=list)
    engine_id: str = "media_gate_v1"

    @property
    def failures(self) -> list[str]:
        return [
            f"{c.section}:{c.path}" + (f" — {c.detail}" if c.detail else "")
            for c in self.checks
            if not c.ok
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "passed": self.passed,
            "failures": self.failures,
            "checks": [asdict(c) for c in self.checks],
        }


class MediaGateError(ValueError):
    """Raised when deliverable is blocked by Section-Aware Media Gate."""

    def __init__(self, result: MediaGateResult):
        self.result = result
        msg = "media_gate_failed: " + "; ".join(result.failures[:8])
        super().__init__(msg)


def _norm_niche(niche_id: str | None) -> str:
    key = (niche_id or "generic").strip().lower() or "generic"
    return key


def showcase_relative(path: Path) -> str | None:
    """Return path relative to showcases/ if under Hero Pack library."""
    parts = path.resolve().parts
    for i, part in enumerate(parts):
        if part == "showcases" and i + 1 < len(parts):
            return "/".join(parts[i + 1 :]).replace("\\", "/")
    return None


def infer_source_niche(path: Path) -> str | None:
    rel = showcase_relative(path)
    if not rel:
        return None
    return rel.split("/", 1)[0].lower() or None


def tags_for_media(
    path: Path | None,
    *,
    source: str = "unknown",
    niche_id: str | None = None,
) -> frozenset[str]:
    """Resolve semantic tags without LLM — ownership + overrides + client trust."""
    if source == "client":
        return frozenset({"client"})
    if path is None:
        return frozenset()

    rel = showcase_relative(path)
    if rel and rel in _TAG_OVERRIDES:
        return _TAG_OVERRIDES[rel]

    src_niche = infer_source_niche(path)
    if src_niche and src_niche in NICHE_DEFAULT_TAGS:
        return NICHE_DEFAULT_TAGS[src_niche]

    # Product-copied asset without showcase ancestry — trust declared niche lightly.
    key = _norm_niche(niche_id)
    if key in NICHE_DEFAULT_TAGS:
        return NICHE_DEFAULT_TAGS[key]
    return frozenset({"untagged"})


def evaluate_section_media(
    *,
    niche_id: str | None,
    section: Section,
    tags: frozenset[str],
    path: str = "",
) -> MediaGateCheck:
    """Answer: does this image belong in this section for this niche?"""
    niche = _norm_niche(niche_id)
    tag_t = tuple(sorted(tags))

    if "client" in tags:
        return MediaGateCheck(
            section=section, path=path, ok=True, tags=tag_t, detail="client_upload"
        )

    if "untagged" in tags:
        return MediaGateCheck(
            section=section,
            path=path,
            ok=False,
            tags=tag_t,
            detail="untagged_media",
        )

    rule = NICHE_RULES.get(niche)
    expect = SECTION_EXPECT.get(section, frozenset())

    if rule:
        denied = tags & rule.deny
        if denied:
            return MediaGateCheck(
                section=section,
                path=path,
                ok=False,
                tags=tag_t,
                detail=f"denied:{','.join(sorted(denied))}",
            )
        if rule.allow and not (tags & rule.allow):
            return MediaGateCheck(
                section=section,
                path=path,
                ok=False,
                tags=tag_t,
                detail="no_allowed_category",
            )

    # Section role: at least one tag must match what the block is for.
    if expect and not (tags & expect):
        return MediaGateCheck(
            section=section,
            path=path,
            ok=False,
            tags=tag_t,
            detail="section_mismatch",
        )

    return MediaGateCheck(section=section, path=path, ok=True, tags=tag_t, detail="ok")


def media_fits_section(
    path: Path,
    *,
    niche_id: str | None,
    section: Section,
    source: str = "niche",
) -> bool:
    tags = tags_for_media(path, source=source, niche_id=niche_id)
    return evaluate_section_media(
        niche_id=niche_id,
        section=section,
        tags=tags,
        path=str(path),
    ).ok


def section_for_slot(slot: str) -> Section:
    key = (slot or "").strip().lower()
    if key in SLOT_TO_SECTION:
        return SLOT_TO_SECTION[key]
    if key.startswith("hero"):
        return "hero"
    if key.startswith("background"):
        return "about"
    return "gallery"


def run_media_gate(
    *,
    niche_id: str | None,
    assignments: list[tuple[Section, Path, str]],
) -> MediaGateResult:
    """Evaluate section→path assignments. Empty list = pass (nothing to judge)."""
    checks: list[MediaGateCheck] = []
    for section, path, source in assignments:
        tags = tags_for_media(path, source=source, niche_id=niche_id)
        checks.append(
            evaluate_section_media(
                niche_id=niche_id,
                section=section,
                tags=tags,
                path=path.as_posix() if path else "",
            )
        )
    passed = all(c.ok for c in checks) if checks else True
    return MediaGateResult(passed=passed, checks=checks)


def run_media_gate_for_product(
    product_dir: Path,
    *,
    niche_id: str | None,
    hero_from_client: bool = False,
) -> MediaGateResult:
    """Gate live product assets before publish / ZIP."""
    assets = product_dir / "assets"
    assignments: list[tuple[Section, Path, str]] = []

    hero = assets / "hero.jpg"
    if hero.is_file():
        assignments.append(
            ("hero", hero, "client" if hero_from_client else "niche")
        )

    # Gallery: client photos only (tagged client → pass)
    client_dir = assets / "client"
    if client_dir.is_dir():
        for p in sorted(client_dir.glob("*")):
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                assignments.append(("gallery", p, "client"))

    # Hero pack slots still present in deliverable
    pack = assets / "hero_pack"
    if pack.is_dir():
        for p in sorted(pack.glob("*.jpg")):
            section = section_for_slot(p.stem)
            # hero.jpg already checked; pack hero_* also used in CSS — check all
            assignments.append((section, p, "pack"))

    bg = assets / "background.jpg"
    if bg.is_file():
        assignments.append(("about", bg, "pack"))

    return run_media_gate(niche_id=niche_id, assignments=assignments)


def assert_media_gate(
    product_dir: Path,
    *,
    niche_id: str | None,
    hero_from_client: bool = False,
) -> MediaGateResult:
    result = run_media_gate_for_product(
        product_dir, niche_id=niche_id, hero_from_client=hero_from_client
    )
    if not result.passed:
        raise MediaGateError(result)
    return result
