"""Business Product BP1.1 — ChatBotBusinessProfile store."""

from __future__ import annotations

from typing import Protocol

from app.portal.chatbot_business_profile import (
    ChatBotBusinessProfile,
    ChatBotInitialConfiguration,
)

ENGINE_ID = "chatbot_business_profile_store_v1"


class ChatBotBusinessProfileStore(Protocol):
    def save_profile(self, profile: ChatBotBusinessProfile) -> None: ...

    def get_for_account(self, account_id: str) -> ChatBotBusinessProfile | None: ...

    def save_configuration(
        self, account_id: str, config: ChatBotInitialConfiguration
    ) -> None: ...

    def get_configuration(
        self, account_id: str
    ) -> ChatBotInitialConfiguration | None: ...


class InMemoryChatBotBusinessProfileStore:
    def __init__(self) -> None:
        self._profiles: dict[str, ChatBotBusinessProfile] = {}
        self._configs: dict[str, ChatBotInitialConfiguration] = {}

    def save_profile(self, profile: ChatBotBusinessProfile) -> None:
        self._profiles[profile.account_id] = profile

    def get_for_account(self, account_id: str) -> ChatBotBusinessProfile | None:
        return self._profiles.get(account_id)

    def save_configuration(
        self, account_id: str, config: ChatBotInitialConfiguration
    ) -> None:
        self._configs[account_id] = config

    def get_configuration(
        self, account_id: str
    ) -> ChatBotInitialConfiguration | None:
        return self._configs.get(account_id)
