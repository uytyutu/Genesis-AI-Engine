"""PT4 — In-memory Business Action store."""

from __future__ import annotations

from typing import Protocol

from app.portal.business_action import BusinessAction

ENGINE_ID = "business_action_store_v1"


class BusinessActionStore(Protocol):
    def save(self, row: BusinessAction) -> None: ...

    def list_for_account(
        self, account_id: str, *, conversation_id: str | None = None
    ) -> list[BusinessAction]: ...


class InMemoryBusinessActionStore:
    def __init__(self) -> None:
        self._rows: dict[str, BusinessAction] = {}

    def save(self, row: BusinessAction) -> None:
        self._rows[row.action_id] = row

    def list_for_account(
        self, account_id: str, *, conversation_id: str | None = None
    ) -> list[BusinessAction]:
        rows = [
            row
            for row in self._rows.values()
            if row.account_id == account_id
            and (
                conversation_id is None
                or row.conversation_id == conversation_id
            )
        ]
        return sorted(rows, key=lambda item: item.created_at, reverse=True)
