"""PT3 — AI Assisted Operations (draft/summary never auto-send)."""

from __future__ import annotations

from app.portal.account import new_account
from app.portal.ai_provider_protocol import AIGenerationResult
from app.portal.chatbot_business_profile_facade import ChatBotBusinessProfileFacade
from app.portal.chatbot_business_profile_store import InMemoryChatBotBusinessProfileStore
from app.portal.conversation import ConversationContext
from app.portal.conversation_facade import ConversationFacade
from app.portal.conversation_store import InMemoryConversationStore, InMemoryMessageStore


class _FixedGateway:
    def generate(self, context: ConversationContext) -> AIGenerationResult:
        assert context.metadata.get("auto_send") is False
        assert context.metadata.get("assistance") is True
        return AIGenerationResult(
            text="Draft: We are happy to help with your appointment.",
            provider_type="stub",
            prepared={"prompt_package_id": "pkg-test", "ready": True},
        )


def _facade_with_profile():
    account = new_account(email="ops@ex.de", display_name="Ops")
    store = InMemoryChatBotBusinessProfileStore()
    profiles = ChatBotBusinessProfileFacade.from_parts(profiles=store)
    profiles.bootstrap(
        account_id=account.account_id,
        industry="dental",
        business_name="Smile",
    )
    conversations = InMemoryConversationStore()
    messages = InMemoryMessageStore()
    facade = ConversationFacade.from_parts(
        profiles=store,
        conversations=conversations,
        messages=messages,
        providers=_FixedGateway(),
    )
    return account, facade, messages


def test_draft_reply_never_auto_sends_and_does_not_persist_assist_message():
    account, facade, messages = _facade_with_profile()
    created = facade.create_conversation(account_id=account.account_id)
    draft = facade.draft_reply(
        account_id=account.account_id,
        conversation_id=created.conversation_id,
    )
    assert draft.auto_sent is False
    assert "appointment" in draft.draft_text.lower() or "Draft" in draft.draft_text
    assert draft.prompt_package_id == "pkg-test"
    # Assistance instruction must not be persisted.
    assert len(messages.list_for_conversation(created.conversation_id)) == 0


def test_review_panel_heuristics():
    account, facade, _messages = _facade_with_profile()
    created = facade.create_conversation(account_id=account.account_id)
    review = facade.review_panel(
        account_id=account.account_id,
        conversation_id=created.conversation_id,
    )
    assert review.priority in {"waiting", "normal", "review", "high"}
    assert review.draft_available is True
    assert review.as_dict()["auto_sent"] is False
