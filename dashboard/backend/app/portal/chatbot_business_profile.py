"""Business Product BP1.1 — ChatBotBusinessProfile domain.

Answers only: what business is this digital employee for?

No AI · no channel SDKs · no providers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "chatbot_business_profile_domain_v1"

IndustryCode = Literal[
    "dental",
    "auto_service",
    "beauty",
    "real_estate",
    "restaurant",
    "ecommerce",
    "other",
]

ALLOWED_INDUSTRIES: frozenset[str] = frozenset(
    {
        "dental",
        "auto_service",
        "beauty",
        "real_estate",
        "restaurant",
        "ecommerce",
        "other",
    }
)


class ChatBotProfileError(ValueError):
    """Invalid ChatBot business profile."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ChatBotBusinessProfile:
    """Business identity for ChatBot — not a conversation runtime."""

    profile_id: str
    account_id: str
    business_name: str
    industry: IndustryCode
    description: str
    language: str
    timezone: str
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChatBotInitialConfiguration:
    """Starter config produced by IndustryTemplate bootstrap — still not AI."""

    greeting: str
    working_hours: str
    faq: tuple[dict[str, str], ...]
    behavior: str
    placeholders: dict[str, str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "greeting": self.greeting,
            "working_hours": self.working_hours,
            "faq": list(self.faq),
            "behavior": self.behavior,
            "placeholders": dict(self.placeholders),
        }


def new_business_profile(
    *,
    account_id: str,
    business_name: str,
    industry: str,
    description: str = "",
    language: str = "ru",
    timezone: str = "Europe/Berlin",
) -> ChatBotBusinessProfile:
    if industry not in ALLOWED_INDUSTRIES:
        raise ChatBotProfileError("unknown_industry")
    name = business_name.strip()
    if not name:
        raise ChatBotProfileError("business_name_required")
    lang = language.strip() or "ru"
    tz = timezone.strip() or "Europe/Berlin"
    now = _utc_now_iso()
    return ChatBotBusinessProfile(
        profile_id=str(uuid4()),
        account_id=account_id,
        business_name=name,
        industry=industry,  # type: ignore[arg-type]
        description=description.strip(),
        language=lang,
        timezone=tz,
        created_at=now,
        updated_at=now,
    )


def apply_profile_update(
    current: ChatBotBusinessProfile,
    *,
    business_name: str | None = None,
    industry: str | None = None,
    description: str | None = None,
    language: str | None = None,
    timezone: str | None = None,
) -> ChatBotBusinessProfile:
    next_industry = current.industry
    if industry is not None:
        if industry not in ALLOWED_INDUSTRIES:
            raise ChatBotProfileError("unknown_industry")
        next_industry = industry  # type: ignore[assignment]
    next_name = current.business_name
    if business_name is not None:
        next_name = business_name.strip()
        if not next_name:
            raise ChatBotProfileError("business_name_required")
    return replace(
        current,
        business_name=next_name,
        industry=next_industry,
        description=(
            description.strip()
            if description is not None
            else current.description
        ),
        language=(language.strip() or current.language)
        if language is not None
        else current.language,
        timezone=(timezone.strip() or current.timezone)
        if timezone is not None
        else current.timezone,
        updated_at=_utc_now_iso(),
    )
