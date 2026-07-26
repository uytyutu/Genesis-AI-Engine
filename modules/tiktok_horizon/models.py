"""Shared data models for TikTok Horizon Stage 1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TrendObservation:
    """One platform signal — patterns emerge from many observations, not a fixed topic list."""

    signal_id: str
    observed_at: str
    topic_tokens: list[str]
    duration_sec: float
    hook_style: str
    editing_style: str
    caption_style: str
    hashtag_pattern: list[str]
    engagement_proxy: float = 0.0
    language: str = "de"
    source: str = "adapter"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TrendRecord:
    trend_id: str
    topic_label: str
    growth_score: float
    average_duration: float
    hook_style: str
    editing_style: str
    caption_style: str
    hashtag_pattern: list[str]
    detected_date: str
    last_updated: str
    observation_count: int = 0
    sample_tokens: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IdeaDraft:
    idea_id: str
    trend_id: str
    title: str
    angle: str
    style_variant: str
    originality_note: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScriptDraft:
    script_id: str
    idea_id: str
    structure: list[str]
    narrator_text: str
    caption: str
    cta: str
    hashtags: list[str]
    hook_seconds: str
    style_variant: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VideoPrompt:
    prompt_id: str
    script_id: str
    prompt_text: str
    duration_sec: int
    composition: str
    pace: str
    atmosphere: str
    style: str
    transitions: str
    created_at: str
    # Stage 1: never sent to a live video API
    video_api_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContentQualityScore:
    originality: float
    structure_diversity: float
    visual_diversity: float
    hook_strength: float
    caption_quality: float
    publishing_readiness: float
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def ready(self) -> bool:
        return self.publishing_readiness >= 0.6 and self.originality >= 0.5


@dataclass
class PublishWindow:
    window_start_local: str
    window_end_local: str
    confidence: float
    confidence_label: str
    reasons: list[str]
    # Explicit: not a virality probability
    not_virality_claim: str = (
        "Confidence = model certainty in timing recommendation, not chance of going viral."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PIPELINE_STATUSES = (
    "generated",
    "review",
    "approved",
    "queued",
    # publish / published reserved for later stages — unused in Stage 1
)
