"""Design Concept Pack — brand design before any site/store HTML.

Virtus Core designs brands. HTML is the last export.
Question to answer: How should THIS company look?
Not: How do we assemble a website?
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONCEPT_PIPELINE: tuple[str, ...] = (
    "brand_discovery",
    "business_psychology",
    "competitor_analysis",
    "design_observatory",
    "moodboard",
    "brand_dna",
    "creative_direction",
    "visual_language",
    "typography",
    "color_system",
    "illustration_strategy",
    "media_strategy",
    "animation_strategy",
    "scene_planning",
    "story_flow",
    "experience_flow",
    "wireframe",
    "high_fidelity_design",
    "owner_preview",
    # html_export — only after owner preview, never first
)

REQUIRED_FOR_READY: tuple[str, ...] = (
    "brand_discovery",
    "business_psychology",
    "moodboard",
    "brand_dna",
    "creative_direction",
    "visual_language",
    "typography",
    "color_system",
    "scene_planning",
    "story_flow",
    "experience_flow",
    "owner_preview",
)


@dataclass
class ConceptStage:
    id: str
    title: str
    decision: str
    status: str = "decided"  # decided | missing | pending_owner

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DesignConceptPack:
    """Full artistic concept for one company — exists before HTML export."""

    business_name: str
    niche_id: str
    package_id: str
    surface: str  # site | store
    stages: list[ConceptStage] = field(default_factory=list)
    artistic_concept: str = ""
    brand_personality: str = ""
    anti_template_tests: list[str] = field(default_factory=list)
    fail_rules: list[str] = field(default_factory=list)
    owner_preview: str = "PENDING_OWNER"
    html_export_allowed: bool = False
    html_export_blocked_reason: str = ""
    fingerprint: str = ""
    generated_at: str = ""
    era_note: str = (
        "Stop assembling sections. Design the brand. "
        "HTML is last export — not first stage."
    )

    def missing_stages(self) -> list[str]:
        by_id = {s.id: s for s in self.stages}
        missing: list[str] = []
        for rid in REQUIRED_FOR_READY:
            st = by_id.get(rid)
            if st is None or not (st.decision or "").strip() or st.status == "missing":
                missing.append(rid)
        return missing

    def is_ready(self) -> bool:
        return not self.missing_stages() and bool(self.artistic_concept.strip())

    def as_dict(self) -> dict[str, Any]:
        return {
            "business_name": self.business_name,
            "niche_id": self.niche_id,
            "package_id": self.package_id,
            "surface": self.surface,
            "pipeline": list(CONCEPT_PIPELINE),
            "stages": [s.as_dict() for s in self.stages],
            "artistic_concept": self.artistic_concept,
            "brand_personality": self.brand_personality,
            "anti_template_tests": list(self.anti_template_tests),
            "fail_rules": list(self.fail_rules),
            "owner_preview": self.owner_preview,
            "html_export_allowed": self.html_export_allowed,
            "html_export_blocked_reason": self.html_export_blocked_reason,
            "fingerprint": self.fingerprint,
            "generated_at": self.generated_at,
            "era_note": self.era_note,
            "before_html": True,
            "missing_stages": self.missing_stages(),
            "concept_ready": self.is_ready(),
        }


# Niche psychology — why strangers trust THIS category
_PSYCHOLOGY: dict[str, str] = {
    "psychology": (
        "Visitor arrives anxious or exhausted. First job is safety and dignity — "
        "not a funnel. Trust comes from calm authority and privacy."
    ),
    "dental": (
        "Fear and cost anxiety dominate. First job is clinical calm and modern care — "
        "pain relief of the mind before treatment."
    ),
    "law": (
        "Visitor needs discreet competence. First job is mandate clarity — "
        "you are in capable hands, not a marble cliché."
    ),
    "fashion": (
        "Desire and identity. First job is taste — the brand must feel curated, "
        "not like a catalog dump."
    ),
    "electronics": (
        "Clarity and confidence in tech. First job is intelligent precision — "
        "product as object of desire, not grid noise."
    ),
    "furniture": (
        "Home imagination. First job is spatial warmth — rooms you want to inhabit, "
        "not SKU tiles."
    ),
}

_COMPETITOR_TRAP: dict[str, str] = {
    "psychology": "Avoid clinic brochures, stock calm-hands, identical sage cards.",
    "dental": "Avoid bright blue dental stock, tooth-icon grids, coupon heroes.",
    "law": "Avoid marble columns, scales-of-justice, navy-serif everywhere.",
    "fashion": "Avoid lookbook clones with empty white and generic sans grids.",
    "electronics": "Avoid Amazon-like density and neon tech clichés.",
    "furniture": "Avoid beige catalog sameness and empty room placeholders.",
}


def _stage(id_: str, title: str, decision: str, status: str = "decided") -> ConceptStage:
    return ConceptStage(id=id_, title=title, decision=decision, status=status)


def build_design_concept(
    *,
    business_name: str,
    niche_id: str,
    package_id: str,
    surface: str = "site",
    studio_direction: dict[str, Any] | None = None,
    allow_html_export: bool = False,
    html_blocked_reason: str = "",
) -> DesignConceptPack:
    """Invent a full design concept for THIS company before HTML."""
    name = (business_name or "Business").strip() or "Business"
    niche = (niche_id or "generic").strip().lower() or "generic"
    pid = (package_id or "business").strip().lower() or "business"
    surf = (surface or "site").strip().lower() or "site"
    d = studio_direction or {}

    brand = d.get("brand_dna") or {}
    mood = d.get("moodboard") or {}
    approach = d.get("studio_approach") or {}
    dna = d.get("dna") or {}
    obs = d.get("observatory") or {}
    taste = d.get("taste") or {}
    scenes = list(d.get("scene_sequence") or [])
    why_hero = str(d.get("why_hero_exists") or brand.get("why_hero_exists") or "").strip()

    feeling = str(brand.get("feeling") or mood.get("emotion") or "modern presence").strip()
    voice = str(brand.get("voice") or "specific, contemporary").strip()
    approach_label = str(approach.get("label") or approach.get("id") or "Boutique").strip()
    type_pair = str(dna.get("typography_pair") or brand.get("type_voice") or "display + calm body")
    color_feeling = str(brand.get("color_feeling") or ", ".join(obs.get("brand_feel") or []) or "considered palette")
    hero_layout = str(d.get("hero_layout") or dna.get("hero_layout") or "immersive")
    composition = ""
    chosen = d.get("chosen") or {}
    if isinstance(chosen, dict):
        composition = str(chosen.get("composition_label") or chosen.get("composition_id") or "")
    if not composition:
        composition = str((d.get("dna") or {}).get("composition") or "original composition")

    psych = _PSYCHOLOGY.get(niche, "Stranger needs a clear emotional reason to stay in the first 5 seconds.")
    trap = _COMPETITOR_TRAP.get(niche, "Avoid constructor ladders and interchangeable section stacks.")

    story = (
        f"{name} opens as a {feeling} brand. "
        f"Voice: {voice}. Approach: {approach_label}. "
        f"Arc: {' → '.join(scenes[:6]) if scenes else 'Scene → Story → Emotion → Experience → Conversion'}."
    )
    artistic = (
        f"Artistic concept: {name} is directed as {approach_label} — not as a niche template. "
        f"Hero job: {why_hero or 'one emotional job before features'}. "
        f"Composition: {composition} ({hero_layout}). "
        f"The whole experience must feel like one brand idea, never Hero→Cards→Section noise."
    )

    if pid == "premium":
        bar = (
            "Premium must exceed Virtus Core `/site` in artistic craft — "
            "wow in 5 seconds or FAIL."
        )
    elif pid == "business":
        bar = "Business must visually match Virtus Core `/site` quality bar."
    else:
        bar = "Starter must feel modern and intentional — never cheap constructor."

    stages = [
        _stage(
            "brand_discovery",
            "Brand Discovery",
            f"{name} ({niche}) — surface={surf}. Discover personality before pages. "
            f"Why choose them: specificity of craft and feeling ({feeling}).",
        ),
        _stage("business_psychology", "Business Psychology", psych),
        _stage(
            "competitor_analysis",
            "Competitor Analysis",
            f"Study principles, never copy. Trap to refuse: {trap} "
            f"Observatory never: {', '.join((obs.get('never') or [])[:4]) or 'templates'}.",
        ),
        _stage(
            "design_observatory",
            "Design Observatory",
            f"Principles for {niche}: feel={', '.join((obs.get('brand_feel') or [])[:3]) or color_feeling}. "
            f"Sources: {', '.join((obs.get('study_sources') or [])[:4]) or 'EU studio craft 2026'}.",
        ),
        _stage(
            "moodboard",
            "Moodboard",
            f"Emotion={mood.get('emotion') or feeling}; "
            f"hero_feeling={mood.get('hero_feeling') or why_hero}; "
            f"atmosphere={mood.get('atmosphere') or 'depth without clutter'}; "
            f"keywords={', '.join(mood.get('keywords') or [])}; "
            f"avoid={', '.join(mood.get('avoid') or [])}.",
        ),
        _stage(
            "brand_dna",
            "Brand DNA",
            f"Personality={feeling}. Voice={voice}. "
            f"Why Hero exists: {why_hero or brand.get('why_hero_exists')}. "
            f"Type voice={brand.get('type_voice') or type_pair}.",
        ),
        _stage(
            "creative_direction",
            "Creative Direction",
            f"Studio approach: {approach_label}. "
            f"{approach.get('thesis') or approach.get('summary') or artistic}",
        ),
        _stage(
            "visual_language",
            "Visual Language",
            f"Language of {approach_label}: composition={composition}, "
            f"hero={hero_layout}, depth and rhythm over card grids. {bar}",
        ),
        _stage(
            "typography",
            "Typography Concept",
            f"Pair/voice: {type_pair}. Must carry character for {niche} — never default Inter stack.",
        ),
        _stage(
            "color_system",
            "Color System",
            f"Color as emotion: {color_feeling}. Palette family={dna.get('palette_family') or 'directed'}. "
            f"Not decoration — feeling.",
        ),
        _stage(
            "illustration_strategy",
            "Illustration Strategy",
            "Prefer photography and spatial atmosphere over clipart. "
            "If illustration: one motif that reinforces brand personality — never stock icon rows.",
        ),
        _stage(
            "media_strategy",
            "Media Strategy",
            "Every image must increase trust or desire. Empty slots and letter placeholders = FAIL. "
            "Media serves the concept, not the other way around.",
        ),
        _stage(
            "animation_strategy",
            "Animation Strategy",
            f"Motion={dna.get('motion') or 'meaningful'}. Every animation needs a reason — "
            "entrance of calm, reveal of craft, never decorative bounce.",
        ),
        _stage(
            "scene_planning",
            "Scene Planning",
            f"Scenes (not sections): {' → '.join(scenes) if scenes else 'scene → story → emotion → experience → conversion'}. "
            f"Each screen = a new stage with its own visual center.",
        ),
        _stage(
            "story_flow",
            "Story Flow",
            story,
        ),
        _stage(
            "experience_flow",
            "Experience Flow",
            f"Stranger path: land → feel brand → understand offer → trust → act. "
            f"Taste={taste.get('verdict') or 'PENDING'} ({taste.get('overall') or '—'}). "
            f"Surface={surf}.",
        ),
        _stage(
            "wireframe",
            "Wireframe",
            f"Structure follows story, not a fixed Hero→Cards→Sections ladder. "
            f"Order derived from scenes/composition ({composition}).",
            status="decided",
        ),
        _stage(
            "high_fidelity_design",
            "High Fidelity Design",
            "Hi-fi decisions live in this concept pack (type, color, composition, motion, media). "
            "Pixel export to HTML only after Owner Preview.",
            status="decided",
        ),
        _stage(
            "owner_preview",
            "Owner Preview",
            "Human reads this concept before any marketing HTML export. "
            "PASS only after: «Да. Я бы купил такой сайт.»",
            status="pending_owner",
        ),
    ]

    fp = hashlib.sha256(
        f"{name}|{niche}|{pid}|{surf}|{approach_label}|{composition}|{feeling}".encode()
    ).hexdigest()[:16]

    blocked = html_blocked_reason.strip()
    if not allow_html_export and not blocked:
        blocked = (
            "Site/store HTML export frozen until Design Concept is owner-reviewed "
            "and artistic concept clears constructor feel (Reality Benchmark FAIL)."
        )

    pack = DesignConceptPack(
        business_name=name,
        niche_id=niche,
        package_id=pid,
        surface=surf,
        stages=stages,
        artistic_concept=artistic,
        brand_personality=f"{name}: {feeling}. Voice: {voice}.",
        anti_template_tests=[
            "Could a stranger confuse this with a website constructor template? → FAIL",
            "Does Business visually match Virtus Core /site? If no → FAIL",
            "Does Premium create wow in 5 seconds? If no → FAIL",
            "Is there an artistic concept — or only prettier sections? If only sections → FAIL",
            "Empty fields / placeholder blocks → FAIL",
        ],
        fail_rules=[
            "Constructor-confusable → Generation FAIL",
            "Below Virtus Core quality → Generation FAIL",
            "Premium without 5s wow → Generation FAIL",
            "Missing artistic concept → Generation FAIL",
            "New features forbidden while demos read as templates",
        ],
        owner_preview="PENDING_OWNER",
        html_export_allowed=bool(allow_html_export),
        html_export_blocked_reason=blocked if not allow_html_export else "",
        fingerprint=fp,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    return pack


def render_concept_markdown(pack: DesignConceptPack) -> str:
    lines = [
        f"# Design Concept — {pack.business_name}",
        "",
        f"**Niche:** {pack.niche_id} · **Package:** {pack.package_id} · **Surface:** {pack.surface}",
        "",
        f"> {pack.era_note}",
        "",
        "## Artistic concept",
        "",
        pack.artistic_concept,
        "",
        "## Brand personality",
        "",
        pack.brand_personality,
        "",
        "## Pipeline decisions",
        "",
    ]
    for s in pack.stages:
        lines.append(f"### {s.title}")
        lines.append("")
        lines.append(s.decision)
        lines.append("")
    lines.extend(
        [
            "## Anti-template tests",
            "",
            *[f"- {t}" for t in pack.anti_template_tests],
            "",
            "## FAIL rules",
            "",
            *[f"- {r}" for r in pack.fail_rules],
            "",
            f"**Owner preview:** {pack.owner_preview}",
            f"**HTML export allowed:** {pack.html_export_allowed}",
        ]
    )
    if pack.html_export_blocked_reason:
        lines.append(f"**Blocked:** {pack.html_export_blocked_reason}")
    lines.append("")
    return "\n".join(lines)


def render_concept_preview_html(pack: DesignConceptPack) -> str:
    """Owner Preview page — design deck, not a fake marketing site."""
    stages_html = []
    for s in pack.stages:
        stages_html.append(
            f'<article class="stage"><h3>{_esc(s.title)}</h3>'
            f"<p>{_esc(s.decision)}</p></article>"
        )
    tests = "".join(f"<li>{_esc(t)}</li>" for t in pack.anti_template_tests)
    blocked = (
        f'<p class="blocked"><strong>HTML export frozen.</strong> {_esc(pack.html_export_blocked_reason)}</p>'
        if not pack.html_export_allowed
        else '<p class="ok">HTML export unlocked — still PENDING_OWNER for PASS.</p>'
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Design Concept — {_esc(pack.business_name)}</title>
<style>
:root {{
  --bg: #0c0d0f;
  --fg: #f4f1ea;
  --muted: #a39e94;
  --line: #2a2c31;
  --accent: #c4a574;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  background: radial-gradient(1200px 600px at 10% -10%, #1a1814 0%, var(--bg) 55%);
  color: var(--fg);
  line-height: 1.55;
}}
header {{
  padding: 12vh 8vw 6vh;
  border-bottom: 1px solid var(--line);
}}
.kicker {{
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 0.72rem;
  color: var(--accent);
  font-family: system-ui, sans-serif;
}}
h1 {{
  font-weight: 500;
  font-size: clamp(2.2rem, 6vw, 4.2rem);
  line-height: 1.05;
  margin: 0.4em 0 0.3em;
  max-width: 14ch;
}}
.lead {{
  max-width: 42rem;
  color: var(--muted);
  font-size: 1.15rem;
}}
main {{ padding: 4vh 8vw 12vh; display: grid; gap: 1.5rem; }}
.stage {{
  border-top: 1px solid var(--line);
  padding-top: 1.25rem;
}}
.stage h3 {{
  margin: 0 0 0.4rem;
  font-size: 1.05rem;
  letter-spacing: 0.04em;
}}
.stage p {{ margin: 0; color: var(--muted); max-width: 52rem; }}
.panel {{
  margin-top: 2rem;
  padding: 1.5rem;
  border: 1px solid var(--line);
  background: rgba(255,255,255,0.02);
}}
.blocked {{ color: #e8b4a0; }}
.ok {{ color: #b7d3b0; }}
ul {{ color: var(--muted); }}
footer {{
  padding: 2rem 8vw 4rem;
  color: var(--muted);
  font-size: 0.85rem;
  font-family: system-ui, sans-serif;
}}
</style>
</head>
<body data-tier="{_esc(pack.package_id)}" data-generation-mode="design_concept_owner_preview" data-surface="{_esc(pack.surface)}">
<header>
  <div class="kicker">Virtus Core · Owner Preview · Design Concept</div>
  <h1>{_esc(pack.business_name)}</h1>
  <p class="lead">{_esc(pack.artistic_concept)}</p>
  <p class="lead">{_esc(pack.brand_personality)}</p>
  {blocked}
</header>
<main>
  <section class="panel">
    <h2>Anti-template tests</h2>
    <ul>{tests}</ul>
  </section>
  {''.join(stages_html)}
</main>
<footer>
  Pipeline ends at Owner Preview. Marketing HTML is last export — not first stage.<br/>
  Fingerprint {_esc(pack.fingerprint)} · { _esc(pack.package_id) } · { _esc(pack.niche_id) } · owner={_esc(pack.owner_preview)}
</footer>
</body>
</html>
"""


def _esc(value: Any) -> str:
    s = str(value or "")
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_concept_pack(product_dir: Path, pack: DesignConceptPack) -> None:
    product_dir.mkdir(parents=True, exist_ok=True)
    (product_dir / "concept_pack.json").write_text(
        json.dumps(pack.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (product_dir / "concept_pack.md").write_text(
        render_concept_markdown(pack),
        encoding="utf-8",
    )
    (product_dir / "OWNER_PREVIEW.md").write_text(
        render_concept_markdown(pack),
        encoding="utf-8",
    )


def write_concept_preview_as_index(product_dir: Path, pack: DesignConceptPack) -> Path:
    """Replace marketing site with Owner Preview until HTML export is unlocked."""
    path = product_dir / "index.html"
    path.write_text(render_concept_preview_html(pack), encoding="utf-8")
    (product_dir / "GENERATION_MODE.json").write_text(
        json.dumps(
            {
                "mode": "design_concept_owner_preview",
                "html_export_allowed": pack.html_export_allowed,
                "reason": pack.html_export_blocked_reason,
                "note": "Marketing HTML frozen. This index is the design concept deck.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path
