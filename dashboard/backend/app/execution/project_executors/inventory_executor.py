"""Inventory executor — VOS plug-in test (Cycle 17). No bridge changes required."""

from __future__ import annotations

import re
from typing import Any

from app.execution.project_executors.spec import ExecutorSpec, register_spec
from app.execution.project_executors.universal import UniversalProjectExecutor

SERVICE_INVENTORY = "inventory"


class InventoryProjectExecutor(UniversalProjectExecutor):
    """Warehouse / inventory automation — stub executor for scalability test."""

    service_id = SERVICE_INVENTORY

    def detect_new_request(self, goal: str) -> bool:
        return bool(
            re.search(r"(?:склад|inventory|учёт\s+товар|остатк)", goal or "", re.I)
            and re.search(r"(?:хочу|нужен|нужна|создай|автоматиз)", goal or "", re.I)
        )


register_spec(
    ExecutorSpec(
        executor=InventoryProjectExecutor(),
        service_ids=frozenset({SERVICE_INVENTORY}),
        intent_patterns=(
            (
                re.compile(
                    r"(?:склад|inventory|учёт\s+товар|остатк|warehouse)",
                    re.I,
                ),
                SERVICE_INVENTORY,
            ),
        ),
    )
)
