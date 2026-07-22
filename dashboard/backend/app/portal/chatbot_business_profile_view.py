"""Business Product BP1.1 — Views for profile / templates / bootstrap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.chatbot_business_profile import (
    ChatBotBusinessProfile,
    ChatBotInitialConfiguration,
)
from app.portal.industry_template import IndustryTemplate

ENGINE_ID = "chatbot_business_profile_view_v1"


@dataclass(frozen=True)
class ChatBotBusinessProfileView:
    profile_id: str
    account_id: str
    business_name: str
    industry: str
    description: str
    language: str
    timezone: str
    created_at: str
    updated_at: str
    initial_configuration: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "profile_id": self.profile_id,
            "account_id": self.account_id,
            "business_name": self.business_name,
            "industry": self.industry,
            "description": self.description,
            "language": self.language,
            "timezone": self.timezone,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.initial_configuration is not None:
            payload["initial_configuration"] = self.initial_configuration
        return payload


@dataclass(frozen=True)
class IndustryTemplateView:
    industry: str
    label: str
    system_prompt_seed: str
    default_faq: list[dict[str, str]]
    default_behavior: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "industry": self.industry,
            "label": self.label,
            "system_prompt_seed": self.system_prompt_seed,
            "default_faq": list(self.default_faq),
            "default_behavior": self.default_behavior,
        }


def build_profile_view(
    profile: ChatBotBusinessProfile,
    *,
    configuration: ChatBotInitialConfiguration | None = None,
) -> ChatBotBusinessProfileView:
    return ChatBotBusinessProfileView(
        profile_id=profile.profile_id,
        account_id=profile.account_id,
        business_name=profile.business_name,
        industry=profile.industry,
        description=profile.description,
        language=profile.language,
        timezone=profile.timezone,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        initial_configuration=(
            configuration.as_dict() if configuration is not None else None
        ),
    )


def build_template_view(template: IndustryTemplate) -> IndustryTemplateView:
    return IndustryTemplateView(
        industry=template.industry,
        label=template.label,
        system_prompt_seed=template.system_prompt_seed,
        default_faq=[dict(item) for item in template.default_faq],
        default_behavior=template.default_behavior,
    )
