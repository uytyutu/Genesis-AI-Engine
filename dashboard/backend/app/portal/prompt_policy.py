"""AI Platform AP2.1 — Policy Layer (behavior rules, vendor-neutral).

```text
Prompt & Policy Layer prepares AI instructions.
Prompt & Policy Layer never calls providers.
Prompt & Policy Layer never modifies Business Knowledge.
Prompt & Policy Layer never communicates with channels.
```
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.conversation import ConversationContext

ENGINE_ID = "prompt_policy_v1"

_INDUSTRY_SAFETY: dict[str, tuple[str, ...]] = {
    "dental": (
        "Do not diagnose medical conditions or prescribe treatment.",
        "For pain or emergencies, advise contacting the clinic directly.",
    ),
    "auto_service": (
        "Do not give dangerous repair instructions that could cause injury.",
    ),
    "beauty": (
        "Do not give medical advice about skin conditions.",
    ),
    "real_estate": (
        "Do not invent property availability, prices, or legal outcomes.",
    ),
    "restaurant": (
        "For allergies, advise confirming with the restaurant staff.",
    ),
    "ecommerce": (
        "Do not invent stock levels, tracking numbers, or refund guarantees.",
    ),
}


@dataclass(frozen=True)
class PromptPolicy:
    language: str
    tone: str
    max_response_sentences: int
    formatting: str
    safety_rules: tuple[str, ...]
    temperature: float
    max_tokens: int
    style_notes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "tone": self.tone,
            "max_response_sentences": self.max_response_sentences,
            "formatting": self.formatting,
            "safety_rules": list(self.safety_rules),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "style_notes": list(self.style_notes),
        }

    def instruction_block(self) -> str:
        lines = [
            f"Reply language: {self.language}.",
            f"Tone: {self.tone}.",
            f"Keep answers to about {self.max_response_sentences} short sentences.",
            f"Formatting: {self.formatting}.",
        ]
        for note in self.style_notes:
            lines.append(note)
        if self.safety_rules:
            lines.append("Safety constraints:")
            lines.extend(f"- {rule}" for rule in self.safety_rules)
        return "\n".join(lines)


def resolve_policy(context: ConversationContext) -> PromptPolicy:
    business = context.business or {}
    template = context.industry_template or {}
    language = str(business.get("language") or "ru").strip() or "ru"
    industry = str(business.get("industry") or template.get("industry") or "other")
    behavior = str(template.get("default_behavior") or "").strip()
    style_notes: list[str] = []
    if behavior:
        style_notes.append(f"Industry behavior: {behavior}")
    style_notes.append("You are Vector, the AI Business Employee for this company.")
    style_notes.append("Use only provided business facts; do not invent details.")
    safety = _INDUSTRY_SAFETY.get(industry, ()) + (
        "If information is missing, say so and offer to connect the customer with the business.",
    )
    return PromptPolicy(
        language=language,
        tone="professional_friendly",
        max_response_sentences=6,
        formatting="plain_text_short_paragraphs",
        safety_rules=safety,
        temperature=0.4,
        max_tokens=800,
        style_notes=tuple(style_notes),
    )
