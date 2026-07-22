"""AI Platform AP2.1 — PromptPackage contract.

Adapters receive this package — not raw ConversationContext assembly logic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

ENGINE_ID = "prompt_package_v1"


@dataclass(frozen=True)
class PromptPackage:
    """Vendor-neutral instruction package for Provider Adapters."""

    package_id: str
    conversation_id: str
    profile_id: str
    system_prompt: str
    business_context: dict[str, Any]
    conversation_history: tuple[dict[str, str], ...]
    user_message: str
    generation_parameters: dict[str, Any]
    policy_snapshot: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "conversation_id": self.conversation_id,
            "profile_id": self.profile_id,
            "system_prompt": self.system_prompt,
            "business_context": dict(self.business_context),
            "conversation_history": [dict(item) for item in self.conversation_history],
            "user_message": self.user_message,
            "generation_parameters": dict(self.generation_parameters),
            "policy_snapshot": dict(self.policy_snapshot),
        }

    def provider_messages(self) -> list[dict[str, str]]:
        """Chat-style messages for adapters — no vendor-specific shaping."""
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}
        ]
        messages.extend(dict(item) for item in self.conversation_history)
        if self.user_message.strip():
            messages.append({"role": "user", "content": self.user_message.strip()})
        return messages


def new_prompt_package(
    *,
    conversation_id: str,
    profile_id: str,
    system_prompt: str,
    business_context: dict[str, Any],
    conversation_history: tuple[dict[str, str], ...] | list[dict[str, str]],
    user_message: str,
    generation_parameters: dict[str, Any],
    policy_snapshot: dict[str, Any] | None = None,
) -> PromptPackage:
    return PromptPackage(
        package_id=str(uuid4()),
        conversation_id=conversation_id,
        profile_id=profile_id,
        system_prompt=system_prompt,
        business_context=dict(business_context),
        conversation_history=tuple(dict(item) for item in conversation_history),
        user_message=user_message,
        generation_parameters=dict(generation_parameters),
        policy_snapshot=dict(policy_snapshot or {}),
    )
