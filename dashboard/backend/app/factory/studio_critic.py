"""Studio Critic — Art Director heuristics after HTML generation (v1, no LLM)."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ExperienceScore:
    story: int  # 0-100
    motion: int
    atmosphere: int
    interaction: int
    media: int
    trust: int
    conversion: int
    overall: int
    portfolio_ready: bool
    template_like: bool
    euro_studio_feel: bool  # feels €5k+ not €500
    rebuild: bool
    critiques: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clamp(n: int) -> int:
    return max(0, min(100, int(n)))


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def run_studio_critic(
    product_dir: Path,
    *,
    niche_id: str = "",
    brand_name: str = "",
    package_id: str = "",
) -> ExperienceScore:
    """Heuristic Art Director pass — writes STUDIO_CRITIC.json + EXPERIENCE_SCORE.json."""
    root = Path(product_dir)
    html_path = root / "index.html"
    html = ""
    html_size = 0
    if html_path.is_file():
        html = html_path.read_text(encoding="utf-8", errors="ignore")
        html_size = len(html.encode("utf-8"))

    brief = _read_json(root / "CREATIVE_BRIEF.json")
    visual = _read_json(root / "VISUAL_BRAND.json")
    media_note = _read_json(root / "PREMIUM_MEDIA_NOTE.json")
    pkg = (package_id or brief.get("package_id") or "").strip().lower()
    premium = pkg in ("premium", "connected")

    has_hero = bool(
        re.search(r'class=["\'][^"\']*\bhero\b', html, re.I)
        or re.search(r'id=["\']hero["\']', html, re.I)
        or "hero" in html.lower()[:8000]
    )
    has_tier = "data-tier" in html or "data-package" in html
    has_3d = "virtus-3d" in html.lower() or "webgl" in html.lower() or "three." in html.lower()
    has_experience_css = bool(
        re.search(r"experience|parallax|magnetic|scroll-reveal|cinematic", html, re.I)
    )
    has_unique_brief = bool(
        brief.get("fingerprint")
        or brief.get("hero_concept")
        or brief.get("visual_metaphor")
        or brief.get("image_prompt")
    )
    concept_only = bool(
        brief.get("concept_only")
        or brief.get("media_mode") == "concept_only"
        or "concept-only" in html.lower()
    )
    offline_only = bool(
        media_note.get("studio_offline_media")
        or str(media_note.get("provider") or "") == "studio_offline"
    )
    has_visual_brand = bool(visual.get("fingerprint") or visual.get("color") or visual)

    critiques: list[str] = []
    strengths: list[str] = []

    # --- dimension scores ---
    story = 42
    if has_unique_brief:
        story += 28
        strengths.append("Creative brief present")
    else:
        critiques.append("Missing unique CREATIVE_BRIEF")
    if brand_name and brand_name.lower() in html.lower():
        story += 12
    if niche_id and niche_id.replace("_", " ") in html.lower():
        story += 8
    if html_size > 80_000:
        story += 10
        strengths.append("Substantial HTML body")
    elif html_size < 25_000:
        story -= 15
        critiques.append("HTML unusually small for a finished site")

    motion = 35
    if has_experience_css:
        motion += 35
        strengths.append("Experience / motion language in CSS")
    else:
        critiques.append("Little motion / experience CSS")
    if "animation" in html.lower() or "@keyframes" in html.lower():
        motion += 15
    if premium and not has_experience_css:
        motion -= 10

    atmosphere = 38
    if has_visual_brand:
        atmosphere += 22
        strengths.append("VISUAL_BRAND.json present")
    if has_experience_css:
        atmosphere += 18
    if has_3d:
        atmosphere += 15
        strengths.append("3D / WebGL accent")
    elif premium:
        critiques.append("No virtus-3d / WebGL accent on premium")
    if offline_only and premium:
        atmosphere -= 12
        critiques.append("Premium on Studio Offline Media only")

    interaction = 40
    if re.search(r"<form|whatsapp|tel:|mailto:|cta|button", html, re.I):
        interaction += 25
        strengths.append("Contact / CTA paths present")
    else:
        critiques.append("Weak interaction / CTA surface")
    if "data-" in html:
        interaction += 10
    if has_hero:
        interaction += 10

    media = 35
    if has_visual_brand:
        media += 20
    if media_note:
        media += 10
        if not offline_only:
            media += 20
            strengths.append(f"Media provider: {media_note.get('provider_label') or media_note.get('provider')}")
        else:
            media += 5
            strengths.append("Studio Offline Media noted honestly")
    if re.search(r"\.(jpg|jpeg|png|webp|svg)", html, re.I):
        media += 15
    else:
        critiques.append("Few image references in HTML")

    trust = 40
    if re.search(r"impressum|datenschutz|review|testimonial|bewertung|trust", html, re.I):
        trust += 30
        strengths.append("Trust / legal signals")
    else:
        critiques.append("Sparse trust / legal signals")
    if re.search(r"€|\bEUR\b|preis|price", html, re.I):
        trust += 10

    conversion = 38
    if re.search(r"cta|jetzt|anfragen|buchen|kontakt|whatsapp|bestell", html, re.I):
        conversion += 30
        strengths.append("Conversion language present")
    else:
        critiques.append("Weak conversion language")
    if has_hero and has_tier:
        conversion += 12
    if premium and html_size > 100_000:
        conversion += 10

    story = _clamp(story)
    motion = _clamp(motion)
    atmosphere = _clamp(atmosphere)
    interaction = _clamp(interaction)
    media = _clamp(media)
    trust = _clamp(trust)
    conversion = _clamp(conversion)

    overall = _clamp(
        int(
            round(
                story * 0.16
                + motion * 0.12
                + atmosphere * 0.16
                + interaction * 0.12
                + media * 0.14
                + trust * 0.14
                + conversion * 0.16
            )
        )
    )

    template_like = bool(
        html_size < 28_000
        or concept_only
        or (not has_unique_brief and html_size < 60_000)
    )
    if template_like:
        critiques.append("Reads template-like (size / concept-only / missing brief)")

    euro_studio_feel = True
    if not has_atmosphere_signal(has_experience_css, has_3d, has_visual_brand):
        euro_studio_feel = False
        critiques.append("Lacks atmosphere / experience depth")
    if premium and offline_only and not has_3d and not has_experience_css:
        euro_studio_feel = False
        critiques.append("Premium offline Pillow without 3D/experience — not €5k studio feel")
    if template_like:
        euro_studio_feel = False
    if euro_studio_feel:
        strengths.append("Euro studio feel signals present")

    portfolio_ready = overall >= 72 and not template_like and euro_studio_feel
    rebuild = overall < 55 or template_like

    score = ExperienceScore(
        story=story,
        motion=motion,
        atmosphere=atmosphere,
        interaction=interaction,
        media=media,
        trust=trust,
        conversion=conversion,
        overall=overall,
        portfolio_ready=portfolio_ready,
        template_like=template_like,
        euro_studio_feel=euro_studio_feel,
        rebuild=rebuild,
        critiques=critiques[:12],
        strengths=strengths[:12],
    )

    critic_payload = {
        "version": 1,
        "niche_id": niche_id,
        "brand_name": brand_name,
        "package_id": pkg,
        "html_bytes": html_size,
        "signals": {
            "has_hero": has_hero,
            "has_tier": has_tier,
            "has_3d": has_3d,
            "has_experience_css": has_experience_css,
            "has_unique_brief": has_unique_brief,
            "concept_only": concept_only,
            "offline_only": offline_only,
            "has_visual_brand": has_visual_brand,
        },
        "score": score.as_dict(),
    }
    (root / "STUDIO_CRITIC.json").write_text(
        json.dumps(critic_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (root / "EXPERIENCE_SCORE.json").write_text(
        json.dumps(score.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return score


def has_atmosphere_signal(has_experience_css: bool, has_3d: bool, has_visual_brand: bool) -> bool:
    return bool(has_experience_css or has_3d or has_visual_brand)


__all__ = ["ExperienceScore", "run_studio_critic"]
