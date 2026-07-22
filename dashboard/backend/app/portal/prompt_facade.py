"""AI Platform AP2.1 — PromptFacade (Prompt & Policy entry)."""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.conversation import ConversationContext
from app.portal.prompt_builder import build_prompt_package
from app.portal.prompt_package import PromptPackage

ENGINE_ID = "prompt_facade_v1"


@dataclass(frozen=True)
class PromptFacade:
    """Prepares PromptPackage only — never calls providers."""

    def build(self, context: ConversationContext) -> PromptPackage:
        return build_prompt_package(context)
