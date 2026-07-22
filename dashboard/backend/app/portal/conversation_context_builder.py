"""Business Product BP1.4 — Context Builder + Knowledge Selection (simple).

Never calls AI · never uses vector retrieval · never talks to providers.
"""

from __future__ import annotations

from app.portal.business_knowledge import ALLOWED_KNOWLEDGE_CATEGORIES
from app.portal.business_knowledge_store import BusinessKnowledgeStore
from app.portal.channel_connection_store import ChannelConnectionStore
from app.portal.chatbot_business_profile import ChatBotBusinessProfile
from app.portal.conversation import (
    Conversation,
    ConversationContext,
    ConversationError,
    DEFAULT_KNOWLEDGE_CATEGORIES,
    Message,
)
from app.portal.industry_template import IndustryTemplateStore

ENGINE_ID = "conversation_context_builder_v1"


def select_knowledge_categories(
    requested: list[str] | None,
) -> tuple[str, ...]:
    if not requested:
        return DEFAULT_KNOWLEDGE_CATEGORIES
    clean: list[str] = []
    for item in requested:
        name = item.strip().lower()
        if name == "all":
            return tuple(sorted(ALLOWED_KNOWLEDGE_CATEGORIES))
        if name not in ALLOWED_KNOWLEDGE_CATEGORIES:
            raise ConversationError(f"unknown_category:{name}")
        if name not in clean:
            clean.append(name)
    if not clean:
        return DEFAULT_KNOWLEDGE_CATEGORIES
    return tuple(clean)


def build_conversation_context(
    *,
    conversation: Conversation,
    profile: ChatBotBusinessProfile,
    messages: tuple[Message, ...],
    knowledge_store: BusinessKnowledgeStore,
    templates: IndustryTemplateStore,
    channels: ChannelConnectionStore,
    selected_categories: tuple[str, ...] | None = None,
) -> ConversationContext:
    categories = selected_categories or DEFAULT_KNOWLEDGE_CATEGORIES
    facts = []
    for row in knowledge_store.list_for_profile(profile.profile_id):
        if row.category in categories:
            facts.append(
                {
                    "knowledge_id": row.knowledge_id,
                    "category": row.category,
                    "title": row.title,
                    "content": row.content,
                }
            )

    template = templates.get(profile.industry)
    template_payload = None
    if template is not None:
        template_payload = {
            "industry": template.industry,
            "label": template.label,
            "system_prompt_seed": template.system_prompt_seed,
            "default_behavior": template.default_behavior,
        }

    channel_meta: dict[str, object] = {}
    if conversation.channel_connection_id:
        channel = channels.get(conversation.channel_connection_id)
        if channel is not None and channel.profile_id == profile.profile_id:
            channel_meta = {
                "channel": channel.channel,
                "display_name": channel.display_name,
                "status": channel.status,
            }

    return ConversationContext(
        conversation_id=conversation.conversation_id,
        profile_id=profile.profile_id,
        business={
            "profile_id": profile.profile_id,
            "business_name": profile.business_name,
            "industry": profile.industry,
            "description": profile.description,
            "language": profile.language,
            "timezone": profile.timezone,
        },
        industry_template=template_payload,
        knowledge=tuple(facts),
        selected_categories=categories,
        messages=tuple(
            {
                "message_id": item.message_id,
                "role": item.role,
                "content": item.content,
                "created_at": item.created_at,
            }
            for item in messages
        ),
        metadata={
            "channel_connection_id": conversation.channel_connection_id,
            "channel": channel_meta,
            "ai_provider": "not_connected",
            "engine": ENGINE_ID,
        },
    )
