"""Revenue Lab — isolated research contour (not Core Business).

Does NOT earn money. Does NOT call farm adapters for payouts.
Only stores researched candidates for CEO review.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LAB_FILE = "revenue_lab_candidates.jsonl"

CONTOURS_RU = {
    "core_business": (
        "Core Business — сайты, агенты, автоматизации, лиды, Stripe. "
        "Главный двигатель выручки."
    ),
    "revenue_lab": (
        "Revenue Lab — исследование легальных моделей. "
        "Не «добыть деньги любой ценой». Эксперимент → CONFIRMED → испытание → Active."
    ),
    "commercial_api": (
        "Commercial API Gateway — клиенты платят Virtus за услуги. Ядро скрыто за Gateway."
    ),
}


def contours() -> dict[str, Any]:
    return {
        "title_ru": "Virtus Core — контуры",
        "law": {
            "id": "FINANCE_REALITY_OVER_SIMULATION",
            "title_ru": "Реальность важнее симуляции",
        },
        "contours": [
            {"id": "core_business", "role": "primary_revenue", "note_ru": CONTOURS_RU["core_business"]},
            {"id": "commercial_api", "role": "product_api", "note_ru": CONTOURS_RU["commercial_api"]},
            {"id": "revenue_lab", "role": "research", "note_ru": CONTOURS_RU["revenue_lab"]},
            {
                "id": "finance_ledger",
                "role": "accounting",
                "note_ru": "Только CONFIRMED / WITHDRAWN / BOOKED. Estimate ≠ Revenue.",
            },
        ],
        "lab_rule_ru": (
            "Lab не обходит ToS и не создаёт аккаунты. "
            "Находка → Candidate → ключ CEO → эксперимент → Reality Law."
        ),
        "passive_income_ru": (
            "Пассивный доход внешних API не предполагается заранее — "
            "только после доказанных поступлений."
        ),
    }


class RevenueLab:
    def __init__(self, memory_dir: Path) -> None:
        self._path = memory_dir / LAB_FILE

    def add_candidate(
        self,
        *,
        name: str,
        api_ok: bool,
        automation_allowed: bool | None,
        payouts: bool | None,
        roi_note: str = "unknown",
        why_ru: str = "",
        source_type: str = "Affiliate",
    ) -> dict[str, Any]:
        row = {
            "id": uuid.uuid4().hex[:12],
            "at": datetime.now(timezone.utc).isoformat(),
            "name": (name or "")[:120],
            "type": source_type,
            "api": bool(api_ok),
            "automation_allowed": automation_allowed,
            "payouts": payouts,
            "roi": roi_note[:80],
            "status": "needs_ceo_account",
            "status_ru": "Нужен аккаунт CEO",
            "why_ru": (why_ru or "Ручной кандидат Revenue Lab")[:500],
            "confidence": "NOT_CONNECTED",
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def list_candidates(self, *, limit: int = 50) -> list[dict[str, Any]]:
        if not self._path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        for line in self._path.read_text(encoding="utf-8").strip().splitlines()[-limit:]:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return list(reversed(rows))
