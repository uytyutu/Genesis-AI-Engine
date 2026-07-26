"""Content Quality — internal scores (NOT virality probability)."""

from __future__ import annotations

from typing import Any

from modules.tiktok_horizon.models import ContentQualityScore, ScriptDraft


class ContentQualityEngine:
    def score(
        self,
        *,
        script: ScriptDraft | dict[str, Any],
        idea: dict[str, Any] | None = None,
        recent_styles: list[str] | None = None,
    ) -> ContentQualityScore:
        if isinstance(script, dict):
            hook = str(script.get("hook_seconds") or "")
            caption = str(script.get("caption") or "")
            narrator = str(script.get("narrator_text") or "")
            style = str(script.get("style_variant") or "")
            structure = list(script.get("structure") or [])
            hashtags = list(script.get("hashtags") or [])
        else:
            hook = script.hook_seconds
            caption = script.caption
            narrator = script.narrator_text
            style = script.style_variant
            structure = list(script.structure)
            hashtags = list(script.hashtags)

        notes: list[str] = []
        originality = 0.75
        if idea and "Original concept" in str(idea.get("originality_note") or ""):
            originality = 0.85
        if "copy" in narrator.lower() or "remake" in narrator.lower():
            originality = min(originality, 0.4)
            notes.append("Narrator mentions copy/remake — review originality.")

        recent = recent_styles or []
        structure_diversity = 0.9 if style not in recent[-3:] else 0.45
        if style in recent[-3:]:
            notes.append("Style repeats recent drafts — consider another variant.")

        visual_diversity = 0.7 if style in ("contrast_cut", "before_after", "owner_story") else 0.6
        hook_strength = min(1.0, 0.35 + len(hook) / 80)
        if len(hook) < 20:
            hook_strength = 0.4
            notes.append("Hook is short — strengthen first 3 seconds.")

        caption_quality = 0.5
        if 20 <= len(caption) <= 280:
            caption_quality = 0.8
        if hashtags:
            caption_quality = min(1.0, caption_quality + 0.1)

        readiness = (
            originality * 0.25
            + structure_diversity * 0.15
            + visual_diversity * 0.15
            + hook_strength * 0.25
            + caption_quality * 0.2
        )
        if len(structure) < 3:
            readiness *= 0.8
            notes.append("Structure too thin.")
        notes.append("Scores are internal quality gates — not virality forecasts.")

        return ContentQualityScore(
            originality=round(originality, 2),
            structure_diversity=round(structure_diversity, 2),
            visual_diversity=round(visual_diversity, 2),
            hook_strength=round(hook_strength, 2),
            caption_quality=round(caption_quality, 2),
            publishing_readiness=round(readiness, 2),
            notes=notes,
        )
