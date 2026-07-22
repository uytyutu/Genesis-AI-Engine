"""Business Product BP1.1 — ChatBotBusinessProfileService.

Profile + IndustryTemplate bootstrap → InitialConfiguration.
Never calls AI or channel SDKs.
"""

from __future__ import annotations

from app.portal.chatbot_business_profile import (
    ChatBotProfileError,
    apply_profile_update,
    new_business_profile,
)
from app.portal.chatbot_business_profile_store import ChatBotBusinessProfileStore
from app.portal.chatbot_business_profile_view import (
    ChatBotBusinessProfileView,
    IndustryTemplateView,
    build_profile_view,
    build_template_view,
)
from app.portal.industry_template import (
    IndustryTemplateStore,
    build_initial_configuration,
)

ENGINE_ID = "chatbot_business_profile_service_v1"


class ChatBotBusinessProfileService:
    def __init__(
        self,
        *,
        profiles: ChatBotBusinessProfileStore,
        templates: IndustryTemplateStore,
    ) -> None:
        self._profiles = profiles
        self._templates = templates

    def get_profile(self, account_id: str) -> ChatBotBusinessProfileView | None:
        row = self._profiles.get_for_account(account_id)
        if row is None:
            return None
        return build_profile_view(
            row,
            configuration=self._profiles.get_configuration(account_id),
        )

    def upsert_profile(
        self,
        *,
        account_id: str,
        business_name: str | None = None,
        industry: str | None = None,
        description: str | None = None,
        language: str | None = None,
        timezone: str | None = None,
    ) -> ChatBotBusinessProfileView:
        current = self._profiles.get_for_account(account_id)
        if current is None:
            if not business_name or not industry:
                raise ChatBotProfileError("profile_bootstrap_required")
            created = new_business_profile(
                account_id=account_id,
                business_name=business_name,
                industry=industry,
                description=description or "",
                language=language or "ru",
                timezone=timezone or "Europe/Berlin",
            )
            self._profiles.save_profile(created)
            return build_profile_view(
                created,
                configuration=self._profiles.get_configuration(account_id),
            )

        updated = apply_profile_update(
            current,
            business_name=business_name,
            industry=industry,
            description=description,
            language=language,
            timezone=timezone,
        )
        self._profiles.save_profile(updated)
        return build_profile_view(
            updated,
            configuration=self._profiles.get_configuration(account_id),
        )

    def list_templates(self) -> list[IndustryTemplateView]:
        return [
            build_template_view(row) for row in self._templates.list_templates()
        ]

    def bootstrap(
        self,
        *,
        account_id: str,
        industry: str,
        business_name: str | None = None,
        description: str | None = None,
        language: str | None = None,
        timezone: str | None = None,
    ) -> ChatBotBusinessProfileView:
        template = self._templates.get(industry)
        if template is None:
            raise ChatBotProfileError("unknown_industry")

        current = self._profiles.get_for_account(account_id)
        name = (
            business_name.strip()
            if business_name and business_name.strip()
            else (current.business_name if current else template.label)
        )
        if current is None:
            profile = new_business_profile(
                account_id=account_id,
                business_name=name,
                industry=industry,
                description=description or "",
                language=language or "ru",
                timezone=timezone or "Europe/Berlin",
            )
        else:
            profile = apply_profile_update(
                current,
                business_name=business_name,
                industry=industry,
                description=description,
                language=language,
                timezone=timezone,
            )

        config = build_initial_configuration(template)
        self._profiles.save_profile(profile)
        self._profiles.save_configuration(account_id, config)
        return build_profile_view(profile, configuration=config)
