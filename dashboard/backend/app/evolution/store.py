"""G3.1 persistence — JSONL under memory/evolution/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, TypeVar

from app.evolution.models import (
    ChangeProposal,
    KnowledgeLedgerEntry,
    LearningQueueItem,
    SupportTicket,
)

T = TypeVar("T")


class EvolutionStore:
    def __init__(self, memory_dir: Path) -> None:
        self._root = memory_dir / "evolution"
        self._root.mkdir(parents=True, exist_ok=True)
        self._tickets = self._root / "tickets.jsonl"
        self._proposals = self._root / "proposals.jsonl"
        self._ledger = self._root / "knowledge_ledger.jsonl"
        self._learning = self._root / "learning_queue.jsonl"

    def append_ticket(self, row: SupportTicket) -> None:
        self._append(self._tickets, row.as_dict())

    def append_proposal(self, row: ChangeProposal) -> None:
        self._append(self._proposals, row.as_dict())

    def append_ledger(self, row: KnowledgeLedgerEntry) -> None:
        self._append(self._ledger, row.as_dict())

    def append_learning(self, row: LearningQueueItem) -> None:
        self._append(self._learning, row.as_dict())

    def list_tickets(self) -> list[SupportTicket]:
        return [
            SupportTicket(**r)
            for r in self._load(self._tickets)
            if self._ok(SupportTicket, r)
        ]

    def list_proposals(self) -> list[ChangeProposal]:
        rows: list[ChangeProposal] = []
        for r in self._load(self._proposals):
            try:
                rows.append(ChangeProposal(**r))
            except TypeError:
                continue
        return rows

    def list_ledger(self) -> list[KnowledgeLedgerEntry]:
        rows: list[KnowledgeLedgerEntry] = []
        for r in self._load(self._ledger):
            try:
                rows.append(KnowledgeLedgerEntry(**r))
            except TypeError:
                continue
        return rows

    def list_learning(self) -> list[LearningQueueItem]:
        rows: list[LearningQueueItem] = []
        for r in self._load(self._learning):
            try:
                rows.append(LearningQueueItem(**r))
            except TypeError:
                continue
        return rows

    def get_proposal(self, proposal_id: str) -> ChangeProposal | None:
        for row in self.list_proposals():
            if row.proposal_id == proposal_id:
                return row
        return None

    def rewrite_proposals(self, rows: list[ChangeProposal]) -> None:
        self._rewrite(self._proposals, [r.as_dict() for r in rows])

    def rewrite_learning(self, rows: list[LearningQueueItem]) -> None:
        self._rewrite(self._learning, [r.as_dict() for r in rows])

    def update_ticket_status(self, ticket_id: str, status: str) -> None:
        tickets = self.list_tickets()
        out: list[dict[str, Any]] = []
        for t in tickets:
            d = t.as_dict()
            if t.ticket_id == ticket_id:
                d["status"] = status
            out.append(d)
        self._rewrite(self._tickets, out)

    @staticmethod
    def _ok(cls: type[T], row: dict[str, Any]) -> bool:
        try:
            cls(**row)  # type: ignore[misc]
            return True
        except TypeError:
            return False

    def _append(self, path: Path, row: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _load(self, path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows

    def _rewrite(self, path: Path, rows: list[dict[str, Any]]) -> None:
        path.write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
            encoding="utf-8",
        )
