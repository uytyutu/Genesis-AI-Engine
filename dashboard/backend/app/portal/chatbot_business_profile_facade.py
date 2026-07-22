"""Business Product BP1.1 — ChatBotBusinessProfileFacade."""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.chatbot_business_profile import ChatBotProfileError
from app.portal.chatbot_business_profile_service import ChatBotBusinessProfileService
from app.portal.chatbot_business_profile_store import (
    ChatBotBusinessProfileStore,
    InMemoryChatBotBusinessProfileStore,
)
from app.portal.chatbot_business_profile_view import (
    ChatBotBusinessProfileView,
    IndustryTemplateView,
)
from app.portal.industry_template import (
    InMemoryIndustryTemplateStore,
    IndustryTemplateStore,
)

ENGINE_ID = "chatbot_business_profile_facade_v1"


@dataclass(frozen=True)
class ChatBotBusinessProfileFacade:
    _service: ChatBotBusinessProfileService

    @classmethod
    def from_parts(
        cls,
        *,
        profiles: ChatBotBusinessProfileStore | None = None,
        templates: IndustryTemplateStore | None = None,
    ) -> ChatBotBusinessProfileFacade:
        return cls(
            _service=ChatBotBusinessProfileService(
                profiles=profiles
                if profiles is not None
                else InMemoryChatBotBusinessProfileStore(),
                templates=templates
                if templates is not None
                else InMemoryIndustryTemplateStore(),
            )
        )

    def get_profile(self, *, account_id: str) -> ChatBotBusinessProfileView | None:
        return self._service.get_profile(account_id)

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
        try:
            return self._service.upsert_profile(
                account_id=account_id,
                business_name=business_name,
                industry=industry,
                description=description,
                language=language,
                timezone=timezone,
            )
        except ChatBotProfileError:
            raise

    def list_templates(self) -> list[IndustryTemplateView]:
        return self._service.list_templates()

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
        try:
            return self._service.bootstrap(
                account_id=account_id,
                industry=industry,
                business_name=business_name,
                description=description,
                language=language,
                timezone=timezone,
            )
        except ChatBotProfileError:
            raise
