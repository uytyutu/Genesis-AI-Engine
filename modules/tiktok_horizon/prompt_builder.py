"""Prompt Builder — text prompts for future AI Video (not executed in Stage 1)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from modules.tiktok_horizon.models import ScriptDraft, VideoPrompt


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_PACE = {
    "quick_tip": "fast cuts, 1 idea per beat",
    "myth_bust": "medium pace, pause on the reveal",
    "before_after": "split rhythm: slow before, punchy after",
    "checklist": "steady checklist beats",
    "owner_story": "conversational, natural pauses",
    "contrast_cut": "hard cuts between wrong/right",
}


class PromptBuilder:
    def build(
        self,
        script: ScriptDraft | dict[str, Any],
        *,
        duration_sec: int | None = None,
    ) -> VideoPrompt:
        if isinstance(script, dict):
            script = ScriptDraft(
                **{k: script[k] for k in ScriptDraft.__dataclass_fields__ if k in script}
            )
        style = script.style_variant or "quick_tip"
        dur = int(duration_sec or 25)
        dur = max(8, min(dur, 60))
        prompt_text = (
            f"Vertical 9:16 short video, {dur}s. Style: {style}. "
            f"Composition: talking-head + B-roll, no logos unless enabled later. "
            f"Pace: {_PACE.get(style, 'medium')}. "
            f"Atmosphere: clean, natural light, authentic (not stock-ad). "
            f"Transitions: soft whip or hard cut matching style. "
            f"Hook (first 3s on-screen text): {script.hook_seconds!r}. "
            f"Narration outline: {script.narrator_text[:500]!r}. "
            "Do NOT recreate any existing viral video. Original visuals only."
        )
        return VideoPrompt(
            prompt_id=f"prompt-{uuid.uuid4().hex[:10]}",
            script_id=script.script_id,
            prompt_text=prompt_text,
            duration_sec=dur,
            composition="9:16 talking-head + B-roll",
            pace=_PACE.get(style, "medium"),
            atmosphere="authentic natural",
            style=style,
            transitions="style-matched",
            created_at=_now(),
            video_api_enabled=False,
        )
