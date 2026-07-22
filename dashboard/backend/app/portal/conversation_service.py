"""Business Product BP1.4 — ConversationService.

Prepares ConversationContext, then asks AI Provider Layer via Protocol only.
Never imports OpenAI/Anthropic/Ollama SDKs.
"""

from __future__ import annotations

from typing import Protocol

from app.portal.ai_provider import STUB_UNAVAILABLE_REPLY
from app.portal.ai_provider_protocol import AIGenerationResult
from app.portal.business_knowledge_store import BusinessKnowledgeStore
from app.portal.channel_connection_store import ChannelConnectionStore
from app.portal.chatbot_business_profile_store import ChatBotBusinessProfileStore
from app.portal.conversation import (
    ConversationContext,
    ConversationError,
    mark_conversation_prepared,
    new_conversation,
    new_message,
    set_conversation_status,
)
from app.portal.conversation_context_builder import (
    build_conversation_context,
    select_knowledge_categories,
)
from app.portal.conversation_store import ConversationStore, MessageStore
from app.portal.conversation_view import (
    ConversationTurnView,
    ConversationView,
    build_conversation_view,
    build_message_view,
    context_as_dict,
)
from app.portal.industry_template import IndustryTemplateStore

ENGINE_ID = "conversation_service_v1"


class AIGenerationGateway(Protocol):
    """Conversation Engine → Provider Layer boundary (Protocol only)."""

    def generate(self, context: ConversationContext) -> AIGenerationResult: ...


class _UnavailableGateway:
    def generate(self, context: ConversationContext) -> AIGenerationResult:
        return AIGenerationResult(
            text=STUB_UNAVAILABLE_REPLY,
            provider_type="none",
            prepared={
                "ready": False,
                "conversation_id": context.conversation_id,
            },
        )


class ConversationService:
    def __init__(
        self,
        *,
        conversations: ConversationStore,
        messages: MessageStore,
        profiles: ChatBotBusinessProfileStore,
        knowledge: BusinessKnowledgeStore,
        channels: ChannelConnectionStore,
        templates: IndustryTemplateStore,
        providers: AIGenerationGateway | None = None,
    ) -> None:
        self._conversations = conversations
        self._messages = messages
        self._profiles = profiles
        self._knowledge = knowledge
        self._channels = channels
        self._templates = templates
        self._providers = providers if providers is not None else _UnavailableGateway()

    def _require_profile(self, account_id: str):
        profile = self._profiles.get_for_account(account_id)
        if profile is None:
            raise ConversationError("profile_required")
        return profile

    def create(
        self,
        *,
        account_id: str,
        channel_connection_id: str | None = None,
    ) -> ConversationView:
        profile = self._require_profile(account_id)
        if channel_connection_id:
            channel = self._channels.get(channel_connection_id)
            if channel is None or channel.profile_id != profile.profile_id:
                raise ConversationError("channel_not_found")
        row = new_conversation(
            profile_id=profile.profile_id,
            channel_connection_id=channel_connection_id,
        )
        self._conversations.save(row)
        return build_conversation_view(row, messages=())

    def list_for_account(self, *, account_id: str) -> list[ConversationView]:
        profile = self._require_profile(account_id)
        rows = sorted(
            self._conversations.list_for_profile(profile.profile_id),
            key=lambda item: item.updated_at,
            reverse=True,
        )
        return [build_conversation_view(row) for row in rows]

    def get(
        self, *, account_id: str, conversation_id: str
    ) -> ConversationView:
        profile = self._require_profile(account_id)
        row = self._conversations.get(conversation_id)
        if row is None or row.profile_id != profile.profile_id:
            raise ConversationError("conversation_not_found")
        messages = self._messages.list_for_conversation(conversation_id)
        return build_conversation_view(row, messages=messages)

    def set_status(
        self,
        *,
        account_id: str,
        conversation_id: str,
        status: str,
    ) -> ConversationView:
        profile = self._require_profile(account_id)
        row = self._conversations.get(conversation_id)
        if row is None or row.profile_id != profile.profile_id:
            raise ConversationError("conversation_not_found")
        updated = set_conversation_status(row, status=status)
        self._conversations.save(updated)
        messages = self._messages.list_for_conversation(conversation_id)
        return build_conversation_view(updated, messages=messages)

    def post_message(
        self,
        *,
        account_id: str,
        conversation_id: str,
        content: str,
        categories: list[str] | None = None,
    ) -> ConversationTurnView:
        profile = self._require_profile(account_id)
        conversation = self._conversations.get(conversation_id)
        if conversation is None or conversation.profile_id != profile.profile_id:
            raise ConversationError("conversation_not_found")
        if conversation.status == "closed":
            raise ConversationError("conversation_closed")

        user_msg = new_message(
            conversation_id=conversation_id, role="user", content=content
        )
        self._messages.save(user_msg)

        history = self._messages.list_for_conversation(conversation_id)
        selected = select_knowledge_categories(categories)
        context = build_conversation_context(
            conversation=conversation,
            profile=profile,
            messages=history,
            knowledge_store=self._knowledge,
            templates=self._templates,
            channels=self._channels,
            selected_categories=selected,
        )

        generation = self._providers.generate(context)
        reply_text = generation.text

        assistant_msg = new_message(
            conversation_id=conversation_id,
            role="assistant",
            content=reply_text,
        )
        self._messages.save(assistant_msg)

        prepared = mark_conversation_prepared(conversation)
        self._conversations.save(prepared)
        all_messages = self._messages.list_for_conversation(conversation_id)

        context_payload = context_as_dict(context)
        context_payload["metadata"] = {
            **context_payload.get("metadata", {}),
            "ai_provider": generation.provider_type,
            "provider_prepared": generation.prepared,
        }

        return ConversationTurnView(
            conversation=build_conversation_view(
                prepared, messages=all_messages
            ),
            user_message=build_message_view(user_msg),
            assistant_message=build_message_view(assistant_msg),
            context=context_payload,
            stub_response=reply_text,
        )
