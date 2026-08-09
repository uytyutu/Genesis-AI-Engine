"""Visual Intelligence Engine — orchestrator for Website · Store · Platform."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from app.factory.design_engine import DesignTokens, FontPack, emit_css_vars, resolve_for_niche
from app.factory.design_engine.fonts import font_pack_for_niche
from app.factory.visual_intelligence.asset_manager import AssetManager, AssetPick
from app.factory.visual_intelligence.motion_engine import (
    MotionPlan,
    emit_motion_css,
    resolve_motion_tier,
)
from app.factory.visual_intelligence.style_engine import (
    StyleProfile,
    components_for_surface,
    normalize_niche,
    resolve_style,
)

VISUAL_ENGINE_ID = "visual_intelligence_v1"
Surface = Literal["website", "store", "platform"]


@dataclass
class VisualPlan:
    engine_id: str
    surface: Surface
    niche_id: str
    style: StyleProfile
    tokens: DesignTokens
    fonts: FontPack
    motion: MotionPlan
    components: tuple[str, ...]
    assets: list[AssetPick] = field(default_factory=list)
    css_vars: str = ""
    motion_css: str = ""
    quality_target: float = 90.0
    package_id: str | None = None

    def body_attributes(self) -> dict[str, str]:
        return {
            "data-vie-engine": self.engine_id,
            "data-vie-surface": self.surface,
            "data-vie-niche": self.niche_id,
            "data-vie-motion": self.motion.tier,
            "data-vie-mood": self.style.mood.split("·")[0].strip()[:48],
        }

    def body_class_extra(self) -> str:
        return self.motion.css_class

    def as_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "surface": self.surface,
            "niche_id": self.niche_id,
            "style": self.style.as_dict(),
            "motion": self.motion.as_dict(),
            "components": list(self.components),
            "assets": [a.as_dict() for a in self.assets],
            "quality_target": self.quality_target,
            "package_id": self.package_id,
            "tokens": {
                "primary": self.tokens.primary,
                "accent": self.tokens.accent,
                "ink": self.tokens.ink,
                "surface": self.tokens.surface,
                "hero_gradient": self.tokens.hero_gradient,
            },
            "body_attributes": self.body_attributes(),
            "body_class": self.body_class_extra(),
        }


def resolve_visual_plan(
    *,
    niche_id: str | None,
    surface: Surface = "website",
    package_id: str | None = None,
    motion_tier: str | None = None,
    prefer_ai_assets: bool = False,
    client_hero: str | None = None,
    memory_dir: Any = None,
    pick_assets: bool = True,
) -> VisualPlan:
    """Single entry — Style + Design tokens + Motion + Assets."""
    niche = normalize_niche(niche_id)
    style = resolve_style(niche)
    tokens = resolve_for_niche(niche)
    fonts = font_pack_for_niche(niche)
    if surface == "platform" and not motion_tier:
        motion_tier = "premium"
    motion = resolve_motion_tier(
        requested=motion_tier,
        style_default=style.motion_default,
        package_id=package_id,
        surface=surface,
    )
    assets: list[AssetPick] = []
    if pick_assets:
        mgr = AssetManager(memory_dir)
        roles = ("hero", "background") if surface != "store" else ("hero", "product", "banner")
        for role in roles:
            assets.append(
                mgr.pick(
                    role=role,
                    niche_id=niche,
                    prefer_ai=prefer_ai_assets,
                    client_path=client_hero if role == "hero" else None,
                )
            )

    return VisualPlan(
        engine_id=VISUAL_ENGINE_ID,
        surface=surface,
        niche_id=niche,
        style=style,
        tokens=tokens,
        fonts=fonts,
        motion=motion,
        components=components_for_surface(surface),
        assets=assets,
        css_vars=emit_css_vars(tokens),
        motion_css=emit_motion_css(motion.tier, surface=surface),
        package_id=package_id,
    )


def apply_visual_plan_to_html(html: str, plan: VisualPlan) -> str:
    """Inject VIE body attributes, motion class, and motion CSS."""
    if not html:
        return html
    out = html

    def _body_repl(m: re.Match[str]) -> str:
        tag = m.group(0)
        for k, v in plan.body_attributes().items():
            esc = v.replace('"', "")
            if k in tag:
                tag = re.sub(rf'{k}="[^"]*"', f'{k}="{esc}"', tag)
            else:
                tag = tag[:-1] + f' {k}="{esc}"' + ">"
        cls = plan.body_class_extra()
        if 'class="' in tag:
            if cls not in tag:
                tag = tag.replace('class="', f'class="{cls} ', 1)
        else:
            tag = tag[:-1] + f' class="{cls}"' + ">"
        return tag

    out = re.sub(r"<body\b[^>]*>", _body_repl, out, count=1, flags=re.I)
    if plan.motion_css and "Visual Intelligence · Motion Engine" not in out:
        snippet = f'<style id="vie-motion">\n{plan.motion_css}\n</style>\n</head>'
        if "</head>" in out:
            out = out.replace("</head>", snippet, 1)
    return out


def _sample_html(plan: VisualPlan) -> str:
    return f"""<!doctype html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/motion_kit.css">
<style>
:root {{ --p: {plan.tokens.primary}; --acc: {plan.tokens.accent}; --ink: {plan.tokens.ink}; --surface: {plan.tokens.surface}; --font-display: Fraunces, serif; }}
@media (max-width: 768px) {{ .hero {{ min-height: 50vh; }} }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>
</head>
<body data-niche="{plan.niche_id}" data-hero-layout="A" data-vie-engine="{plan.engine_id}" class="{plan.body_class_extra()}">
<header class="hero"><h1 class="hero-text">Studio</h1></header>
<section class="section" data-vie-section>Services</section>
<section class="section" data-vie-section>Contact</section>
<img src="assets/library/x.jpg" alt="Atmosphere" loading="lazy">
</body></html>"""


def visual_intelligence_ready(memory_dir: Any = None) -> bool:
    """Gen1 readiness: engine present + sample plans pass Visual Quality Gate ≥ 90."""
    from app.factory.visual_intelligence.quality_gate import run_visual_quality_gate

    try:
        samples = [
            resolve_visual_plan(niche_id="law", surface="website", package_id="business"),
            resolve_visual_plan(niche_id="restaurant", surface="website", package_id="premium"),
            resolve_visual_plan(niche_id="dental", surface="store", package_id="premium"),
            resolve_visual_plan(niche_id="computer", surface="platform", package_id="premium"),
        ]
    except Exception:
        return False

    for plan in samples:
        meta = {
            "niche": plan.niche_id,
            "surface": plan.surface,
            "primary": plan.tokens.primary,
            "accent": plan.tokens.accent,
            "ink": plan.tokens.ink,
            "surface_token": plan.tokens.surface,
            "visual_plan": True,
            "assets": [a.as_dict() for a in plan.assets if a.quality_score >= 70],
        }
        result = run_visual_quality_gate(_sample_html(plan), meta=meta)
        if not result.passed:
            return False
    return True
