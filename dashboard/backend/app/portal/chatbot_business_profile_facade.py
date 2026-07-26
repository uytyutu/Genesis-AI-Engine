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

    def preview_setup(self, *, answers: dict) -> dict:
        from app.portal.bot_setup_questionnaire import build_setup_preview

        return build_setup_preview(answers)

    def publish_setup(self, *, account_id: str, answers: dict) -> dict:
        """Client self-serve publish — no CEO approve."""
        from app.portal.bot_setup_questionnaire import (
            build_configuration,
            build_greeting,
            build_system_prompt,
            knowledge_rows,
            parse_answers,
        )
        from app.portal.chatbot_business_profile import ChatBotInitialConfiguration

        parsed = parse_answers(answers)
        view = self.bootstrap(
            account_id=account_id,
            industry=parsed.industry,
            business_name=parsed.business_name,
            description=parsed.what_company_does,
            language=parsed.language,
            timezone=parsed.timezone,
        )
        config = build_configuration(parsed)
        placeholders = dict(config.placeholders)
        placeholders["setup_status"] = "published"
        placeholders["system_prompt"] = build_system_prompt(parsed)
        published = ChatBotInitialConfiguration(
            greeting=build_greeting(parsed),
            working_hours=config.working_hours,
            faq=config.faq,
            behavior=config.behavior,
            placeholders=placeholders,
        )
        self._service.save_configuration(account_id, published)
        refreshed = self.get_profile(account_id=account_id)
        return {
            "ok": True,
            "status": "published",
            "profile": (refreshed or view).as_dict(),
            "greeting": published.greeting,
            "system_prompt": placeholders["system_prompt"],
            "configuration": published.as_dict(),
            "knowledge": knowledge_rows(parsed),
            "ceo_approve_required": False,
            "message_ru": "Цифровой сотрудник опубликован. Клиент может пользоваться сразу.",
        }
