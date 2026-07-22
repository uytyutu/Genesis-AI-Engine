"""Business Product BP1.4 — ConversationFacade."""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.business_knowledge_store import (
    BusinessKnowledgeStore,
    InMemoryBusinessKnowledgeStore,
)
from app.portal.channel_connection_store import (
    ChannelConnectionStore,
    InMemoryChannelConnectionStore,
)
from app.portal.chatbot_business_profile_store import ChatBotBusinessProfileStore
from app.portal.conversation import ConversationError
from app.portal.conversation_service import ConversationService
from app.portal.conversation_store import (
    ConversationStore,
    InMemoryConversationStore,
    InMemoryMessageStore,
    MessageStore,
)
from app.portal.conversation_view import ConversationTurnView, ConversationView
from app.portal.industry_template import (
    InMemoryIndustryTemplateStore,
    IndustryTemplateStore,
)

ENGINE_ID = "conversation_facade_v1"


@dataclass(frozen=True)
class ConversationFacade:
    _service: ConversationService

    @classmethod
    def from_parts(
        cls,
        *,
        profiles: ChatBotBusinessProfileStore,
        knowledge: BusinessKnowledgeStore | None = None,
        channels: ChannelConnectionStore | None = None,
        templates: IndustryTemplateStore | None = None,
        conversations: ConversationStore | None = None,
        messages: MessageStore | None = None,
    ) -> ConversationFacade:
        return cls(
            _service=ConversationService(
                conversations=conversations
                if conversations is not None
                else InMemoryConversationStore(),
                messages=messages if messages is not None else InMemoryMessageStore(),
                profiles=profiles,
                knowledge=knowledge
                if knowledge is not None
                else InMemoryBusinessKnowledgeStore(),
                channels=channels
                if channels is not None
                else InMemoryChannelConnectionStore(),
                templates=templates
                if templates is not None
                else InMemoryIndustryTemplateStore(),
            )
        )

    def create_conversation(
        self,
        *,
        account_id: str,
        channel_connection_id: str | None = None,
    ) -> ConversationView:
        try:
            return self._service.create(
                account_id=account_id,
                channel_connection_id=channel_connection_id,
            )
        except ConversationError:
            raise

    def list_conversations(self, *, account_id: str) -> list[ConversationView]:
        try:
            return self._service.list_for_account(account_id=account_id)
        except ConversationError:
            raise

    def get_conversation(
        self, *, account_id: str, conversation_id: str
    ) -> ConversationView:
        try:
            return self._service.get(
                account_id=account_id, conversation_id=conversation_id
            )
        except ConversationError:
            raise

    def post_message(
        self,
        *,
        account_id: str,
        conversation_id: str,
        content: str,
        categories: list[str] | None = None,
    ) -> ConversationTurnView:
        try:
            return self._service.post_message(
                account_id=account_id,
                conversation_id=conversation_id,
                content=content,
                categories=categories,
            )
        except ConversationError:
            raise
