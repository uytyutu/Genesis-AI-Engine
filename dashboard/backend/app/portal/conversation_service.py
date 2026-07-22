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
    Message,
    mark_conversation_prepared,
    new_conversation,
    new_message,
    set_conversation_status,
)
from app.portal.conversation_assistance_view import (
    AssistanceDraftView,
    AssistanceReviewView,
    AssistanceSummaryView,
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
from app.portal.prompt_facade import PromptFacade

ENGINE_ID = "conversation_service_v1"

_DRAFT_INSTRUCTION = (
    "OPERATOR ASSIST ONLY — draft a reply the human operator can review. "
    "Do not claim the message was already sent to the customer. "
    "Write only the customer-facing draft text."
)

_SUMMARY_INSTRUCTION = (
    "OPERATOR ASSIST ONLY — summarize this conversation for the business owner "
    "in 3-5 short sentences. Do not write a customer reply."
)


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

    def _load_owned_conversation(self, *, account_id: str, conversation_id: str):
        profile = self._require_profile(account_id)
        conversation = self._conversations.get(conversation_id)
        if conversation is None or conversation.profile_id != profile.profile_id:
            raise ConversationError("conversation_not_found")
        messages = self._messages.list_for_conversation(conversation_id)
        return profile, conversation, messages

    def _assist_generate(
        self,
        *,
        account_id: str,
        conversation_id: str,
        instruction: str,
    ) -> tuple[AIGenerationResult, str | None, str | None]:
        profile, conversation, messages = self._load_owned_conversation(
            account_id=account_id, conversation_id=conversation_id
        )
        # Ephemeral operator instruction — never persisted · never auto-sent.
        assist_msg = new_message(
            conversation_id=conversation_id,
            role="user",
            content=instruction,
        )
        history = tuple(messages) + (assist_msg,)
        context = build_conversation_context(
            conversation=conversation,
            profile=profile,
            messages=history,
            knowledge_store=self._knowledge,
            templates=self._templates,
            channels=self._channels,
            selected_categories=select_knowledge_categories(None),
        )
        # Ensure assistance marker in metadata for Prompt/Policy consumers.
        context = ConversationContext(
            conversation_id=context.conversation_id,
            profile_id=context.profile_id,
            business=context.business,
            industry_template=context.industry_template,
            knowledge=context.knowledge,
            selected_categories=context.selected_categories,
            messages=context.messages,
            metadata={
                **dict(context.metadata),
                "assistance": True,
                "auto_send": False,
            },
        )
        package = PromptFacade().build(context)
        generation = self._providers.generate(context)
        package_id = None
        if isinstance(generation.prepared, dict):
            package_id = generation.prepared.get("prompt_package_id") or package.package_id
        language = None
        if isinstance(package.generation_parameters, dict):
            language = package.generation_parameters.get("language")
        return generation, package_id, language

    def draft_reply(
        self, *, account_id: str, conversation_id: str
    ) -> AssistanceDraftView:
        generation, package_id, language = self._assist_generate(
            account_id=account_id,
            conversation_id=conversation_id,
            instruction=_DRAFT_INSTRUCTION,
        )
        return AssistanceDraftView(
            conversation_id=conversation_id,
            draft_text=generation.text,
            provider_type=generation.provider_type,
            prompt_package_id=str(package_id) if package_id else None,
            policy_language=str(language) if language else None,
            auto_sent=False,
        )

    def summarize(
        self, *, account_id: str, conversation_id: str
    ) -> AssistanceSummaryView:
        generation, package_id, _language = self._assist_generate(
            account_id=account_id,
            conversation_id=conversation_id,
            instruction=_SUMMARY_INSTRUCTION,
        )
        return AssistanceSummaryView(
            conversation_id=conversation_id,
            summary_text=generation.text,
            provider_type=generation.provider_type,
            prompt_package_id=str(package_id) if package_id else None,
            auto_sent=False,
        )

    def review_panel(
        self, *, account_id: str, conversation_id: str
    ) -> AssistanceReviewView:
        _profile, conversation, messages = self._load_owned_conversation(
            account_id=account_id, conversation_id=conversation_id
        )
        text_blob = " ".join(m.content.lower() for m in messages)
        tags: list[str] = []
        if any(w in text_blob for w in ("price", "cost", "€", "цена", "preis")):
            tags.append("pricing")
        if any(w in text_blob for w in ("hour", "open", "время", "öffnungs")):
            tags.append("working_hours")
        if any(w in text_blob for w in ("book", "appoint", "запис", "termin")):
            tags.append("booking")
        if not tags:
            tags.append("general")

        priority = "normal"
        if conversation.status == "open" and len(messages) == 0:
            priority = "waiting"
        elif any(w in text_blob for w in ("urgent", "asap", "срочно", "dringend")):
            priority = "high"
        elif conversation.status == "prepared":
            priority = "review"

        suggested_knowledge: list[dict[str, str]] = []
        if "pricing" in tags:
            suggested_knowledge.append(
                {
                    "category": "pricing",
                    "title": "Clarify pricing fact",
                    "reason": "Customer mentioned price — verify Knowledge pricing.",
                }
            )
        if "working_hours" in tags:
            suggested_knowledge.append(
                {
                    "category": "working_hours",
                    "title": "Confirm opening hours",
                    "reason": "Hours mentioned — keep Knowledge current.",
                }
            )

        insights = [
            f"Status: {conversation.status}",
            f"Messages: {len(messages)}",
            "AI drafts never auto-send — operator decides.",
        ]
        return AssistanceReviewView(
            conversation_id=conversation_id,
            priority=priority,
            suggested_tags=tags,
            suggested_knowledge=suggested_knowledge,
            insights=insights,
            draft_available=True,
            summary_available=True,
        )

    def publish_assistant_message(
        self,
        *,
        account_id: str,
        conversation_id: str,
        content: str,
    ) -> ConversationView:
        """Operator-approved outbound message — no AI call · no auto-send path."""
        profile = self._require_profile(account_id)
        conversation = self._conversations.get(conversation_id)
        if conversation is None or conversation.profile_id != profile.profile_id:
            raise ConversationError("conversation_not_found")
        if conversation.status == "closed":
            raise ConversationError("conversation_closed")
        assistant_msg = new_message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
        )
        self._messages.save(assistant_msg)
        prepared = mark_conversation_prepared(conversation)
        self._conversations.save(prepared)
        all_messages = self._messages.list_for_conversation(conversation_id)
        return build_conversation_view(prepared, messages=all_messages)

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
