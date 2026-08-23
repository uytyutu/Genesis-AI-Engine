"""Creative Identity Generation — €50k agency thinking.

Not: How does a psychologist website look?
But: Who is the human behind this practice — and what idea can you feel?

HTML forbidden until Creative Identity exists and Creative Conflict is clean.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SPRINT_NAME = "Creative Identity Generation"
IDENTITY_PIPELINE: tuple[str, ...] = (
    "human_first",  # person before niche label
    "brand_story",
    "core_emotion",
    "core_promise",
    "visual_metaphor",
    "creative_theme",
    "scene_language",
    "motion_language",
    "typography_voice",
    "color_emotion",
    "interaction_style",
    "creative_conflict",
    "owner_preview",
    # html_export — last, never first
)


@dataclass(frozen=True)
class HumanFirstBrief:
    """Know the human before the niche word."""

    founder_name: str
    founder_role: str
    client_age_range: str
    why_choose_them: str
    visitor_must_feel: str
    niche_revealed_later: str  # filled AFTER identity is invented

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CreativeTheme:
    """Named brand idea — not a niche skin."""

    id: str
    title: str  # e.g. Silent Forest
    idea: str  # feeling you can sense — not a layout
    domains: tuple[str, ...]  # later niches that can wear this idea
    scene_language: str
    motion_language: str
    typography_voice: str
    color_emotion: str
    interaction_style: str
    visual_metaphor: str
    photo_world: str
    forbidden: tuple[str, ...]  # Creative Conflict triggers

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# Named ideas — invent brands, not niches
CREATIVE_THEMES: tuple[CreativeTheme, ...] = (
    # Care / therapy / calm professions
    CreativeTheme(
        "silent_forest",
        "Silent Forest",
        "After a heavy day, a person can finally exhale.",
        ("psychology", "dental", "wellness", "spa"),
        "hushed rooms, deep green quiet, one path inward",
        "slow breathe — fade like mist, never bounce",
        "soft humanist serif + quiet sans — never tech display",
        "deep moss, fog grey, warm wood — never neon",
        "gentle, unhurried, no hard sell",
        "a clearing in the trees where noise stops",
        "forest edge at dusk, empty chair, soft window light",
        ("tech_saas", "gaming", "corporate_office", "neon", "stock_handshake", "coupon_hero"),
    ),
    CreativeTheme(
        "morning_light",
        "Morning Light",
        "Every day can begin again.",
        ("psychology", "dental", "fitness", "beauty", "coaching"),
        "dawn windows, soft gold, open horizon",
        "soft rise — light enters the frame",
        "optimistic editorial — clear, warm, awake",
        "cream, pale gold, sky blue breath",
        "inviting, hopeful, one clear next step",
        "first light through linen curtains",
        "morning desk, coffee steam, open notebook",
        ("noir_club", "gaming", "aggressive_sale", "dark_corporate"),
    ),
    CreativeTheme(
        "safe_space",
        "Safe Space",
        "A place where nobody judges you.",
        ("psychology", "law", "dental", "education"),
        "protected chamber, soft boundaries, human scale",
        "stillness — micro-motion only for reassurance",
        "warm readable — never cold legal marble",
        "soft clay, ivory, muted sage",
        "listening UI — calm forms, quiet confirmations",
        "a room that holds you without asking questions first",
        "empty sofa, soft lamp, closed door that feels safe",
        ("tech_saas", "gaming", "flash_sale", "stock_teeth_smile"),
    ),
    # Dental
    CreativeTheme(
        "precision",
        "Precision",
        "Care so exact it feels effortless.",
        ("dental", "medical", "optics"),
        "clean geometry, focused instrument light, white space with purpose",
        "precise micro-reveals — surgical timing, not bounce",
        "technical clarity + human warmth in body",
        "porcelain white, cool steel, one warm accent",
        "confident, exact, never clinical fear",
        "light on a single instrument — craft not clinic",
        "macro detail, clean gloves, calm clinician eyes",
        ("fire_smoke", "gaming", "coupon_hero", "cartoon_tooth"),
    ),
    CreativeTheme(
        "smile_studio",
        "Smile Studio",
        "Beauty of a smile as a creative craft.",
        ("dental", "beauty", "fashion"),
        "atelier light, portrait focus, editorial framing",
        "elegant reveal of face and detail",
        "fashion-editorial display + soft body",
        "warm ivory, blush, soft charcoal",
        "studio booking — glamorous but human",
        "portrait studio for the smile",
        "softbox portrait, natural smile, craft tools aside",
        ("corporate_office", "gaming", "neon", "stock_family_park"),
    ),
    CreativeTheme(
        "family_care",
        "Family Care",
        "Trust that feels like home for every age.",
        ("dental", "psychology", "pediatric", "medical"),
        "warm home light, multi-generation presence, soft corners",
        "gentle transitions — never startling",
        "friendly humanist — clear for all ages",
        "soft peach, cream, sky calm",
        "reassuring, simple paths, no jargon walls",
        "kitchen-table trust in a clinic",
        "parent and child calm moment, soft daylight",
        ("luxury_noir", "gaming", "aggressive_sale"),
    ),
    # Law
    CreativeTheme(
        "quiet_mandate",
        "Quiet Mandate",
        "Power that does not need to shout.",
        ("law", "finance", "consulting"),
        "measured negative space, one decisive statement",
        "slow authority — no flash",
        "classic serif discipline + modern sans clarity",
        "ink, stone, restrained gold",
        "discreet CTAs — prestige without marble cliché",
        "a closed folder that already holds the answer",
        "desk lamp, clean papers, city dusk through glass",
        ("gaming", "neon", "scales_of_justice_stock", "coupon"),
    ),
    # Restaurant
    CreativeTheme(
        "fire_smoke",
        "Fire & Smoke",
        "Appetite born from heat and craft.",
        ("restaurant", "food", "grill", "feinkost"),
        "ember glow, close heat, dark atmosphere with life",
        "flicker and rise — heat language",
        "bold condensed display + honest body",
        "charcoal, ember orange, smoke grey",
        "urgent desire — reserve now",
        "flame under the plate",
        "grill glow, hands plating, steam",
        ("silent_forest", "tech_saas", "pastel_clinic", "corporate_office"),
    ),
    CreativeTheme(
        "mediterranean_evening",
        "Mediterranean Evening",
        "Long table, warm night, belonging.",
        ("restaurant", "food", "travel"),
        "lantern light, terracotta, shared plates",
        "slow dusk settle — wine pour pace",
        "romantic serif + soft sans",
        "terracotta, olive, deep night blue",
        "welcome, linger, book a table",
        "evening terrace above the sea",
        "table set at dusk, bread, glasses",
        ("nordic_sterile", "gaming", "neon", "tech_saas"),
    ),
    CreativeTheme(
        "nordic_kitchen",
        "Nordic Kitchen",
        "Honest ingredients, quiet excellence.",
        ("restaurant", "food", "furniture"),
        "pale wood, daylight honesty, craft plating",
        "clean cuts — no theatrical smoke",
        "nordic clarity — restrained display",
        "birch, linen, soft grey-green",
        "precise, calm reservation",
        "a plate like a landscape",
        "seasonal produce, linen, pale wood table",
        ("fire_smoke_extreme", "gaming", "neon", "baroque_gold"),
    ),
    # Fashion / commerce
    CreativeTheme(
        "atelier_night",
        "Atelier Night",
        "Clothes as quiet luxury after dark.",
        ("fashion", "beauty", "jewelry"),
        "black room, single garment light, runway hush",
        "slow pan, fabric breath",
        "high-fashion display — sparse words",
        "ink black, champagne, skin tone warmth",
        "lookbook desire — add with restraint",
        "one garment under a spotlight",
        "editorial model, fabric detail, night studio",
        ("family_care", "gaming", "neon_sale", "grid_amazon"),
    ),
    CreativeTheme(
        "signal_clarity",
        "Signal Clarity",
        "Technology that feels intelligent, not loud.",
        ("electronics", "saas", "auto"),
        "precision grids, object hero, cool depth",
        "crisp snaps — engineered, not playful gaming",
        "modern geometric + highly readable body",
        "graphite, electric blue breath, pure white",
        "configure / choose with confidence",
        "a product as a signal in the dark",
        "product on infinite black, soft rim light",
        ("fire_smoke", "mediterranean_evening", "pastel_cute", "gaming_rgb"),
    ),
    CreativeTheme(
        "lived_in_room",
        "Lived-In Room",
        "Furniture that already belongs to a life.",
        ("furniture", "interior", "home", "realestate"),
        "real rooms, soft daylight, human traces",
        "slow settle into space",
        "warm editorial — home story first",
        "oak, linen, soft clay, muted green",
        "browse like walking through a home",
        "an empty chair that still feels occupied",
        "morning living room, book on table, plant",
        ("tech_saas", "gaming", "neon", "warehouse_grid"),
    ),
)


@dataclass
class CreativeConflictVerdict:
    ok: bool
    action: str  # CONTINUE | FAIL
    conflicts: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CreativeIdentity:
    """Digital identity of a business — before site, store, ads, social."""

    title: str  # Silent Forest
    theme_id: str
    idea: str
    human: dict[str, Any]
    brand_story: str
    core_emotion: str
    core_promise: str
    visual_metaphor: str
    creative_theme: str
    scene_language: str
    motion_language: str
    typography_voice: str
    color_emotion: str
    interaction_style: str
    photo_world: str
    niche_revealed: str
    package_id: str
    surface: str
    conflict: dict[str, Any] = field(default_factory=dict)
    forbidden: list[str] = field(default_factory=list)
    owner_preview: str = "PENDING_OWNER"
    html_export_allowed: bool = False
    html_blocked_reason: str = ""
    fingerprint: str = ""
    generated_at: str = ""
    sprint: str = SPRINT_NAME
    agency_note: str = (
        "Think like a creative agency director on a €50,000 brief. "
        "No idea → no HTML. Creative Identity becomes site, store, social, video, ads."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "pipeline": list(IDENTITY_PIPELINE),
            "before_html": True,
            "naming": "Creative Identity — not Concept",
            "question": "Who is the human — and what idea can you feel?",
            "not_question": "How do we assemble a psychologist website?",
        }


def _normalize_domain(niche_id: str) -> str:
    n = (niche_id or "generic").strip().lower()
    aliases = {
        "computer": "electronics",
        "computers": "electronics",
        "tech": "electronics",
        "gadget": "electronics",
        "gadgets": "electronics",
        "apparel": "fashion",
        "clothing": "fashion",
        "clothes": "fashion",
        "home": "furniture",
        "interior": "furniture",
        "interiors": "furniture",
        "realestate": "furniture",
        "real_estate": "furniture",
        "realty": "furniture",
        "food": "restaurant",
        "feinkost": "restaurant",
        "accessories": "fashion",
        "uhren": "fashion",
        "auto": "auto",
        "car": "auto",
        "garage": "auto",
        "handwerk": "handwerk",
        "dachreinigung": "handwerk",
        "dach": "handwerk",
        "zaunbau": "handwerk",
        "zaun": "handwerk",
        "gartenpflege": "green",
        "garten": "green",
        "fitness": "fitness",
        "beauty": "beauty",
        "salon": "beauty",
        "it": "electronics",
        "software": "electronics",
    }
    return aliases.get(n, n)


def _pick_theme(
    *,
    niche_id: str,
    diversity_salt: str,
    business_name: str,
) -> CreativeTheme:
    niche = _normalize_domain(niche_id)
    pool = [t for t in CREATIVE_THEMES if niche in t.domains]
    if not pool:
        # Still not a free-for-all: prefer non-conflicting general craft themes
        pool = [
            t
            for t in CREATIVE_THEMES
            if t.id
            in {
                "morning_light",
                "safe_space",
                "quiet_mandate",
                "atelier_night",
                "signal_clarity",
                "lived_in_room",
            }
        ]
    h = int(
        hashlib.sha256(f"{business_name}|{niche}|{diversity_salt}|identity".encode()).hexdigest()[:8],
        16,
    )
    return pool[h % len(pool)]


def invent_human_first(
    *,
    business_name: str,
    niche_id: str,
    diversity_salt: str = "",
    founder_hint: str = "",
) -> HumanFirstBrief:
    """Invent the person before revealing the niche label."""
    name = (business_name or "Studio").strip() or "Studio"
    niche = (niche_id or "generic").strip().lower()
    # Derive a founder first name from business / salt — never start from "Psychology"
    if founder_hint.strip():
        founder = founder_hint.strip().split()[0]
    else:
        seeds = ("Anna", "Jonas", "Mila", "Erik", "Sofia", "Noah", "Lea", "Max", "Clara", "Felix")
        h = int(hashlib.sha256(f"{name}|{diversity_salt}|founder".encode()).hexdigest()[:6], 16)
        founder = seeds[h % len(seeds)]

    why_by_niche = {
        "psychology": "She knows how to listen — really listen.",
        "dental": "They make precision feel gentle.",
        "law": "Quiet competence without theatrics.",
        "restaurant": "The room makes you want to stay.",
        "fashion": "Taste you can trust without shouting.",
        "electronics": "Clarity — tech without confusion.",
        "furniture": "Pieces that already feel like home.",
    }
    feel_by_niche = {
        "psychology": "relief",
        "dental": "calm confidence",
        "law": "protected clarity",
        "restaurant": "appetite and belonging",
        "fashion": "desire with dignity",
        "electronics": "intelligent certainty",
        "furniture": "settled warmth",
    }
    role_by_niche = {
        "psychology": "founder of the practice",
        "dental": "lead clinician",
        "law": "managing counsel",
        "restaurant": "chef & host",
        "fashion": "creative director",
        "electronics": "product curator",
        "furniture": "atelier founder",
    }
    return HumanFirstBrief(
        founder_name=founder,
        founder_role=role_by_niche.get(niche, "founder"),
        client_age_range="30–50",
        why_choose_them=why_by_niche.get(niche, "They are specific — not interchangeable."),
        visitor_must_feel=feel_by_niche.get(niche, "trust and desire to stay"),
        niche_revealed_later=niche,
    )


def _ban_appears_as_positive_cue(blob: str, ban: str) -> bool:
    """True when a forbidden token is used as a style cue — not as a negation.

    Brand books often write «kein Neon-Salon» / «never neon». That is compliance
    with the ban, not a Creative Conflict. Naive substring matching falsely FAIL'd
    beauty exports and froze marketing HTML into identity-preview decks.
    """
    ban_l = (ban or "").lower().replace("_", " ").strip()
    if not ban_l:
        return False
    blob_l = (blob or "").lower().replace("_", " ")
    first = ban_l.split()[0]
    if first not in blob_l and ban_l not in blob_l:
        return False
    for match in re.finditer(re.escape(first), blob_l):
        left = blob_l[max(0, match.start() - 28) : match.start()]
        if re.search(
            r"(?:kein(?:e|en)?|nie|never|no|not|without|ohne)[\s\-]*$",
            left,
        ):
            continue
        return True
    return False


def check_creative_conflict(
    theme: CreativeTheme,
    *,
    approach_id: str = "",
    hero_hint: str = "",
    motion_hint: str = "",
    type_hint: str = "",
) -> CreativeConflictVerdict:
    """Everything must serve the Creative Theme — or FAIL."""
    conflicts: list[str] = []
    blob = " ".join(
        [
            (approach_id or "").lower(),
            (hero_hint or "").lower(),
            (motion_hint or "").lower(),
            (type_hint or "").lower(),
        ]
    )
    for ban in theme.forbidden:
        if _ban_appears_as_positive_cue(blob, ban):
            conflicts.append(f"Theme '{theme.title}' conflicts with '{ban}'")
    # Hard semantic conflicts
    if theme.id == "silent_forest" and ("tech" in blob or "saas" in blob or "gaming" in blob):
        conflicts.append("Silent Forest cannot speak Tech SaaS / Gaming")
    if theme.id == "silent_forest" and ("corporate" in blob or "office" in blob):
        conflicts.append("Silent Forest cannot open on Corporate Office hero")
    if theme.id.startswith("fire") and ("pastel" in blob or "clinic" in blob):
        conflicts.append("Fire & Smoke cannot feel pastel clinic")
    if "gaming" in blob and theme.id in {"silent_forest", "safe_space", "quiet_mandate", "family_care"}:
        conflicts.append(f"{theme.title} rejects Gaming motion language")

    # Dedupe
    uniq = list(dict.fromkeys(conflicts))
    if uniq:
        return CreativeConflictVerdict(ok=False, action="FAIL", conflicts=uniq)
    return CreativeConflictVerdict(ok=True, action="CONTINUE", conflicts=[])


def invent_creative_identity(
    *,
    business_name: str,
    niche_id: str,
    package_id: str = "business",
    surface: str = "site",
    diversity_salt: str = "",
    approach_id: str = "",
    hero_hint: str = "",
    motion_hint: str = "",
    type_hint: str = "",
    allow_html_export: bool = False,
    html_blocked_reason: str = "",
    founder_hint: str = "",
) -> CreativeIdentity:
    """Human first → named Creative Theme → full identity chain → conflict check."""
    name = (business_name or "Business").strip() or "Business"
    niche = (niche_id or "generic").strip().lower() or "generic"
    pid = (package_id or "business").strip().lower() or "business"
    surf = (surface or "site").strip().lower() or "site"

    human = invent_human_first(
        business_name=name,
        niche_id=niche,
        diversity_salt=diversity_salt,
        founder_hint=founder_hint,
    )
    theme = _pick_theme(niche_id=niche, diversity_salt=diversity_salt, business_name=name)

    # Align type/motion hints with theme when empty (identity leads)
    type_use = type_hint.strip() or theme.typography_voice
    motion_use = motion_hint.strip() or theme.motion_language
    hero_use = hero_hint.strip() or theme.visual_metaphor

    conflict = check_creative_conflict(
        theme,
        approach_id=approach_id,
        hero_hint=hero_use,
        motion_hint=motion_use,
        type_hint=type_use,
    )

    brand_story = (
        f"{human.founder_name} built {name} because {human.why_choose_them.lower()} "
        f"Clients ({human.client_age_range}) should feel {human.visitor_must_feel}. "
        f"Only then do we name the craft: {human.niche_revealed_later}."
    )
    core_emotion = human.visitor_must_feel
    core_promise = theme.idea
    fp = hashlib.sha256(
        f"{name}|{theme.id}|{human.founder_name}|{pid}|{surf}|{diversity_salt}".encode()
    ).hexdigest()[:16]

    blocked = html_blocked_reason.strip()
    if not allow_html_export and not blocked:
        blocked = (
            "No Creative Identity → no HTML. "
            "Unlock only after Owner feels the idea — not the niche template."
        )
    if not conflict.ok:
        allow_html_export = False
        blocked = f"Creative Conflict FAIL: {'; '.join(conflict.conflicts)}"

    return CreativeIdentity(
        title=theme.title,
        theme_id=theme.id,
        idea=theme.idea,
        human=human.as_dict(),
        brand_story=brand_story,
        core_emotion=core_emotion,
        core_promise=core_promise,
        visual_metaphor=theme.visual_metaphor,
        creative_theme=theme.title,
        scene_language=theme.scene_language,
        motion_language=theme.motion_language,
        typography_voice=type_use,
        color_emotion=theme.color_emotion,
        interaction_style=theme.interaction_style,
        photo_world=theme.photo_world,
        niche_revealed=niche,
        package_id=pid,
        surface=surf,
        conflict=conflict.as_dict(),
        forbidden=list(theme.forbidden),
        owner_preview="PENDING_OWNER",
        html_export_allowed=bool(allow_html_export) and conflict.ok,
        html_blocked_reason=blocked,
        fingerprint=fp,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def render_identity_markdown(identity: CreativeIdentity) -> str:
    h = identity.human
    lines = [
        f"# Creative Identity — {identity.title}",
        "",
        f"**Business:** {h.get('founder_name', '')} · {identity.niche_revealed} · {identity.package_id}",
        "",
        f"> {identity.agency_note}",
        "",
        "## The idea (feel this first)",
        "",
        f"**{identity.title}** — {identity.idea}",
        "",
        "## Human first (niche comes later)",
        "",
        f"- Founder: {h.get('founder_name')} ({h.get('founder_role')})",
        f"- Clients: {h.get('client_age_range')}",
        f"- Why them: {h.get('why_choose_them')}",
        f"- Must feel: {h.get('visitor_must_feel')}",
        f"- Niche revealed after: {identity.niche_revealed}",
        "",
        "## Brand DNA (art-director chain)",
        "",
        f"- **Brand Story:** {identity.brand_story}",
        f"- **Core Emotion:** {identity.core_emotion}",
        f"- **Core Promise:** {identity.core_promise}",
        f"- **Visual Metaphor:** {identity.visual_metaphor}",
        f"- **Creative Theme:** {identity.creative_theme}",
        f"- **Scene Language:** {identity.scene_language}",
        f"- **Motion Language:** {identity.motion_language}",
        f"- **Typography Voice:** {identity.typography_voice}",
        f"- **Color Emotion:** {identity.color_emotion}",
        f"- **Interaction Style:** {identity.interaction_style}",
        f"- **Photo World:** {identity.photo_world}",
        "",
        "## Creative Conflict",
        "",
        f"Status: {identity.conflict.get('action')} · ok={identity.conflict.get('ok')}",
        "",
        *[f"- FAIL if present: {f}" for f in identity.forbidden],
        "",
        f"**Owner:** {identity.owner_preview}",
        f"**HTML export:** {identity.html_export_allowed}",
    ]
    if identity.html_blocked_reason:
        lines.append(f"**Blocked:** {identity.html_blocked_reason}")
    lines.append("")
    return "\n".join(lines)


def render_identity_preview_html(identity: CreativeIdentity) -> str:
    h = identity.human
    conflicts = identity.conflict.get("conflicts") or []
    conflict_html = (
        "<ul>" + "".join(f"<li>{_esc(c)}</li>" for c in conflicts) + "</ul>"
        if conflicts
        else "<p>No conflicts — identity is internally coherent.</p>"
    )
    blocked = (
        f'<p class="blocked"><strong>HTML frozen.</strong> {_esc(identity.html_blocked_reason)}</p>'
        if not identity.html_export_allowed
        else '<p class="ok">HTML export unlocked — Owner PASS still required.</p>'
    )
    chain = [
        ("Brand Story", identity.brand_story),
        ("Core Emotion", identity.core_emotion),
        ("Core Promise", identity.core_promise),
        ("Visual Metaphor", identity.visual_metaphor),
        ("Creative Theme", identity.creative_theme),
        ("Scene Language", identity.scene_language),
        ("Motion Language", identity.motion_language),
        ("Typography Voice", identity.typography_voice),
        ("Color Emotion", identity.color_emotion),
        ("Interaction Style", identity.interaction_style),
        ("Photo World", identity.photo_world),
    ]
    stages = "".join(
        f'<article class="stage"><h3>{_esc(t)}</h3><p>{_esc(b)}</p></article>' for t, b in chain
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{_esc(identity.title)} — Creative Identity</title>
<style>
:root {{
  --bg:#0b0c0a; --fg:#f3efe6; --muted:#9e988c; --line:#2a2924; --accent:#c8b48a;
}}
*{{box-sizing:border-box}}
body{{
  margin:0;
  font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  background:radial-gradient(900px 500px at 80% -10%,#1c1a14 0%,var(--bg) 55%);
  color:var(--fg); line-height:1.55;
}}
header{{padding:14vh 8vw 7vh;border-bottom:1px solid var(--line)}}
.kicker{{letter-spacing:.2em;text-transform:uppercase;font-size:.7rem;color:var(--accent);
  font-family:system-ui,sans-serif}}
h1{{font-weight:500;font-size:clamp(2.6rem,7vw,5rem);line-height:1.02;margin:.35em 0 .25em;max-width:12ch}}
.idea{{font-size:clamp(1.2rem,2.4vw,1.65rem);max-width:28rem;color:var(--fg);margin:0 0 1rem}}
.lead{{max-width:40rem;color:var(--muted)}}
main{{padding:4vh 8vw 12vh;display:grid;gap:1.25rem}}
.human{{border:1px solid var(--line);padding:1.25rem 1.4rem;background:rgba(255,255,255,.02)}}
.stage{{border-top:1px solid var(--line);padding-top:1.1rem}}
.stage h3{{margin:0 0 .35rem;font-size:.95rem;letter-spacing:.05em}}
.stage p{{margin:0;color:var(--muted);max-width:52rem}}
.blocked{{color:#e8b4a0}}.ok{{color:#b7d3b0}}
footer{{padding:2rem 8vw 4rem;color:var(--muted);font-size:.85rem;font-family:system-ui,sans-serif}}
</style>
</head>
<body data-tier="{_esc(identity.package_id)}" data-generation-mode="creative_identity_owner_preview" data-surface="{_esc(identity.surface)}" data-theme="{_esc(identity.theme_id)}">
<header>
  <div class="kicker">Virtus Core · Creative Identity · €50k brief thinking</div>
  <h1>{_esc(identity.title)}</h1>
  <p class="idea">{_esc(identity.idea)}</p>
  <p class="lead">Not a niche template. A brand idea you can feel — before HTML exists.</p>
  {blocked}
</header>
<main>
  <section class="human">
    <h2>Human first</h2>
    <p class="lead">
      <strong>{_esc(h.get('founder_name'))}</strong> — {_esc(h.get('founder_role'))}.
      Clients {_esc(h.get('client_age_range'))}.
      Why them: {_esc(h.get('why_choose_them'))}.
      Must feel: <em>{_esc(h.get('visitor_must_feel'))}</em>.
      Niche named only after: {_esc(identity.niche_revealed)}.
    </p>
  </section>
  {stages}
  <section class="stage">
    <h3>Creative Conflict</h3>
    {conflict_html}
  </section>
</main>
<footer>
  { _esc(SPRINT_NAME) } · fingerprint {_esc(identity.fingerprint)} · owner={_esc(identity.owner_preview)}<br/>
  Creative Identity becomes site, store, social, video, ads — HTML is only one export.
  Forbidden when incoherent: {_esc(', '.join(identity.forbidden[:6]))}.
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


def write_creative_identity(product_dir: Path, identity: CreativeIdentity) -> None:
    product_dir.mkdir(parents=True, exist_ok=True)
    (product_dir / "creative_identity.json").write_text(
        json.dumps(identity.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    md = render_identity_markdown(identity)
    (product_dir / "creative_identity.md").write_text(md, encoding="utf-8")
    (product_dir / "OWNER_PREVIEW.md").write_text(md, encoding="utf-8")
    # Compatibility aliases during rename from "concept"
    (product_dir / "concept_pack.json").write_text(
        json.dumps(
            {
                "renamed_to": "creative_identity.json",
                "sprint": SPRINT_NAME,
                "identity": identity.as_dict(),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_identity_preview_as_index(product_dir: Path, identity: CreativeIdentity) -> Path:
    path = product_dir / "index.html"
    path.write_text(render_identity_preview_html(identity), encoding="utf-8")
    (product_dir / "GENERATION_MODE.json").write_text(
        json.dumps(
            {
                "mode": "creative_identity_owner_preview",
                "sprint": SPRINT_NAME,
                "theme": identity.title,
                "html_export_allowed": identity.html_export_allowed,
                "reason": identity.html_blocked_reason,
                "note": "Marketing HTML frozen. This index is the Creative Identity deck.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path
