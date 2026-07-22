"""Business Product BP1.4 — ConversationService.

Prepares ConversationContext + stub assistant reply. Never calls AI.
"""

from __future__ import annotations

from app.portal.business_knowledge_store import BusinessKnowledgeStore
from app.portal.channel_connection_store import ChannelConnectionStore
from app.portal.chatbot_business_profile_store import ChatBotBusinessProfileStore
from app.portal.conversation import (
    ConversationError,
    STUB_ASSISTANT_REPLY,
    mark_conversation_prepared,
    new_conversation,
    new_message,
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
    ) -> None:
        self._conversations = conversations
        self._messages = messages
        self._profiles = profiles
        self._knowledge = knowledge
        self._channels = channels
        self._templates = templates

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

        assistant_msg = new_message(
            conversation_id=conversation_id,
            role="assistant",
            content=STUB_ASSISTANT_REPLY,
        )
        self._messages.save(assistant_msg)

        prepared = mark_conversation_prepared(conversation)
        self._conversations.save(prepared)
        all_messages = self._messages.list_for_conversation(conversation_id)

        return ConversationTurnView(
            conversation=build_conversation_view(
                prepared, messages=all_messages
            ),
            user_message=build_message_view(user_msg),
            assistant_message=build_message_view(assistant_msg),
            context=context_as_dict(context),
            stub_response=STUB_ASSISTANT_REPLY,
        )
