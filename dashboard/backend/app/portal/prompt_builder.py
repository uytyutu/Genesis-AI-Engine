"""AI Platform AP2.1 — Prompt Builder.

Assembles PromptPackage from ConversationContext + Policy.
Never calls providers · never writes Business Knowledge · never talks to channels.
"""

from __future__ import annotations

from typing import Any

from app.portal.conversation import ConversationContext
from app.portal.prompt_package import PromptPackage, new_prompt_package
from app.portal.prompt_policy import PromptPolicy, resolve_policy

ENGINE_ID = "prompt_builder_v1"


def _split_history_and_user(
    messages: tuple[dict[str, Any], ...]
) -> tuple[list[dict[str, str]], str]:
    history: list[dict[str, str]] = []
    user_message = ""
    for item in messages:
        role = str(item.get("role") or "user")
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        if role not in {"user", "assistant", "system"}:
            role = "user"
        history.append({"role": role, "content": content})
    if history and history[-1]["role"] == "user":
        user_message = history[-1]["content"]
        history = history[:-1]
    # Drop prior system rows from history — system lives in system_prompt.
    history = [row for row in history if row["role"] != "system"]
    return history, user_message


def _business_context_block(context: ConversationContext) -> str:
    business = context.business or {}
    template = context.industry_template or {}
    lines: list[str] = []
    if business.get("business_name"):
        lines.append(f"Business name: {business['business_name']}")
    if business.get("industry"):
        lines.append(f"Industry: {business['industry']}")
    if business.get("description"):
        lines.append(f"Description: {business['description']}")
    if business.get("timezone"):
        lines.append(f"Timezone: {business['timezone']}")
    if template.get("system_prompt_seed"):
        lines.append(f"Industry seed: {template['system_prompt_seed']}")
    if context.knowledge:
        lines.append("Business knowledge:")
        for item in context.knowledge:
            lines.append(
                f"- [{item.get('category', '')}] {item.get('title', '')}: "
                f"{item.get('content', '')}"
            )
    return "\n".join(lines)


def build_system_prompt(context: ConversationContext, policy: PromptPolicy) -> str:
    parts = [
        "You are Vector — the AI Business Employee powered by Virtus Core.",
        policy.instruction_block(),
        "Business context:",
        _business_context_block(context) or "(no business facts provided)",
    ]
    return "\n\n".join(parts).strip()


def build_prompt_package(context: ConversationContext) -> PromptPackage:
    """Build PromptPackage without mutating ConversationContext or Knowledge."""
    policy = resolve_policy(context)
    history, user_message = _split_history_and_user(context.messages)
    system_prompt = build_system_prompt(context, policy)
    return new_prompt_package(
        conversation_id=context.conversation_id,
        profile_id=context.profile_id,
        system_prompt=system_prompt,
        business_context=dict(context.business or {}),
        conversation_history=history,
        user_message=user_message,
        generation_parameters={
            "temperature": policy.temperature,
            "max_tokens": policy.max_tokens,
            "language": policy.language,
            "tone": policy.tone,
        },
        policy_snapshot=policy.as_dict(),
    )
