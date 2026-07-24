"""Revenue Lab — research contour: find legal income models, ask CEO to connect.

Does not invent payouts. Does not open farm core to clients.
Produces CEO actions: «подключи X — потому что может дать доход Y (гипотеза)».
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LAB_FILE = "revenue_lab_candidates.jsonl"
ALERTS_FILE = "revenue_lab_ceo_alerts.jsonl"

CONTOURS_RU = {
    "core_business": (
        "Core Business — сайты, агенты, автоматизации, лиды, Stripe. Главный двигатель."
    ),
    "revenue_lab": (
        "Revenue Lab — ищет легальные модели (API+ценность). "
        "Не обходит ToS. Не обещает пассивный доход без доказательства."
    ),
    "commercial_api": (
        "Commercial API — клиенты платят Virtus. Gateway изолирует ядро."
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
                "note_ru": "Только CONFIRMED / WITHDRAWN / BOOKED.",
            },
        ],
        "lab_rule_ru": (
            "Lab ищет, где API позволяет создать ценность. "
            "Доход — только после CEO-ключа и первой CONFIRMED операции."
        ),
    }


# Curated opportunity templates — not web scrape. Lab ranks + CEO prompts.
_OPPORTUNITY_SEED: tuple[dict[str, Any], ...] = (
    {
        "id": "stripe_merchant",
        "name": "Stripe (клиентские оплаты)",
        "type": "Merchant",
        "env_vars": ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"],
        "api_ok": True,
        "automation_allowed": True,
        "payouts": True,
        "model_ru": "Клиент платит Virtus → webhook → Ledger BOOKED",
        "ceo_action_ru": "Проверь Stripe live + webhook в .env.local / Railway",
        "income_hypothesis_ru": (
            "Прямой CONFIRMED доход Core Business (сайты, ремонт, API-пакеты). "
            "Без Stripe коммерческий контур не закрывается."
        ),
        "priority": 1,
        "uses_farm": False,
        "uses_commercial_api": True,
    },
    {
        "id": "virtus_api_audit",
        "name": "Virtus API · Audit (продажа своей возможности)",
        "type": "Merchant",
        "env_vars": [],
        "api_ok": True,
        "automation_allowed": True,
        "payouts": True,
        "model_ru": "Внешний клиент → Gateway → audit → prepaid баланс",
        "ceo_action_ru": (
            "Создай API-ключ (Starter) и отдай первому тестовому клиенту / агентству"
        ),
        "income_hypothesis_ru": (
            "Доход от продажи анализа сайтов через API. "
            "Ферма не нужна клиенту — только Gateway. Первая оплата пакета = доказательство."
        ),
        "priority": 2,
        "uses_farm": False,
        "uses_commercial_api": True,
    },
    {
        "id": "awin_affiliate",
        "name": "Awin (партнёрские комиссии)",
        "type": "Affiliate",
        "env_vars": ["AWIN_API_TOKEN", "AWIN_PUBLISHER_ID"],
        "api_ok": True,
        "automation_allowed": True,
        "payouts": True,
        "model_ru": "Рекомендация сервиса клиенту → комиссия после покупки",
        "ceo_action_ru": "Зарегистрируй publisher на Awin → вставь AWIN_API_TOKEN",
        "income_hypothesis_ru": (
            "Ферма/анализ видит потребность клиента → подбирает продукт → "
            "комиссия только после реальной продажи (не микрозадачи)."
        ),
        "priority": 3,
        "uses_farm": True,
        "uses_commercial_api": False,
    },
    {
        "id": "digistore24_affiliate",
        "name": "Digistore24 (партнёрка DE/EU)",
        "type": "Affiliate",
        "env_vars": ["DIGISTORE24_API_KEY"],
        "api_ok": True,
        "automation_allowed": True,
        "payouts": True,
        "model_ru": "IPN/API учёта конверсий → комиссия",
        "ceo_action_ru": "Создай аккаунт Digistore24 → DIGISTORE24_API_KEY в .env.local",
        "income_hypothesis_ru": (
            "Цифровые продукты + партнёрская ссылка после аудита сайта клиента. "
            "Выплата после подтверждённой продажи."
        ),
        "priority": 4,
        "uses_farm": True,
        "uses_commercial_api": False,
    },
    {
        "id": "open_data_monitor",
        "name": "Мониторинг открытых данных → отчёт клиенту",
        "type": "DataService",
        "env_vars": [],
        "api_ok": True,
        "automation_allowed": True,
        "payouts": False,
        "model_ru": "Внешний data API как инструмент → продажа отчёта через Virtus API/Stripe",
        "ceo_action_ru": (
            "Выбери нишу отчёта (цены/вакансии/недвижимость) — Lab не подключает ключи сама"
        ),
        "income_hypothesis_ru": (
            "Деньги не от data API, а от клиента за отчёт. "
            "Ферма может собирать и нормализовать данные в фоне."
        ),
        "priority": 5,
        "uses_farm": True,
        "uses_commercial_api": True,
    },
)


def _env_ok(names: list[str]) -> bool:
    if not names:
        return True
    return all(bool(os.getenv(n, "").strip()) for n in names)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RevenueLab:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._path = memory_dir / LAB_FILE
        self._alerts = memory_dir / ALERTS_FILE

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
            "at": _now(),
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
        self._append(self._path, row)
        return row

    def list_candidates(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return self._read_jsonl(self._path, limit=limit)

    def research_scan(self, *, persist_alerts: bool = True) -> dict[str, Any]:
        """Rank curated opportunities; emit CEO connect actions. No fake earnings."""
        findings: list[dict[str, Any]] = []
        ceo_actions: list[dict[str, Any]] = []

        for seed in sorted(_OPPORTUNITY_SEED, key=lambda s: int(s.get("priority") or 99)):
            connected = _env_ok(list(seed.get("env_vars") or []))
            status = "ready" if connected else "needs_ceo"
            status_ru = "Ключи на месте" if connected else "Нужен аккаунт / ключ CEO"
            finding = {
                "id": seed["id"],
                "name": seed["name"],
                "type": seed["type"],
                "api": seed["api_ok"],
                "automation_allowed": seed["automation_allowed"],
                "payouts": seed["payouts"],
                "connected": connected,
                "status": status,
                "status_ru": status_ru,
                "model_ru": seed["model_ru"],
                "income_hypothesis_ru": seed["income_hypothesis_ru"],
                "ceo_action_ru": seed["ceo_action_ru"],
                "uses_farm": seed["uses_farm"],
                "uses_commercial_api": seed["uses_commercial_api"],
                "confidence": "CONNECTED_KEYS" if connected else "NOT_CONNECTED",
                "reality_note_ru": (
                    "Гипотеза дохода — не запись в Ledger. "
                    "CONFIRMED только после реальной выплаты/оплаты."
                ),
            }
            findings.append(finding)
            if not connected:
                action = {
                    "id": f"act-{seed['id']}",
                    "priority": seed["priority"],
                    "source_id": seed["id"],
                    "title_ru": f"Подключи: {seed['name']}",
                    "action_ru": seed["ceo_action_ru"],
                    "why_income_ru": seed["income_hypothesis_ru"],
                    "env_vars": seed.get("env_vars") or [],
                    "at": _now(),
                }
                ceo_actions.append(action)
                if persist_alerts:
                    self._append(self._alerts, action)

        ceo_actions.sort(key=lambda a: int(a.get("priority") or 99))
        top = ceo_actions[0] if ceo_actions else None
        return {
            "ok": True,
            "scanned_at": _now(),
            "findings": findings,
            "ceo_actions": ceo_actions,
            "headline_ru": (
                top["title_ru"] + " — " + top["why_income_ru"]
                if top
                else "Все известные кандидаты с ключами закрыты — можно искать новую нишу вручную."
            ),
            "rule_ru": (
                "Lab не создаёт аккаунты и не принимает ToS. "
                "Она говорит CEO, что подключить, чтобы открыть путь к доходу."
            ),
            "contours": contours(),
        }

    def ceo_brief(self) -> dict[str, Any]:
        scan = self.research_scan(persist_alerts=False)
        return {
            "title_ru": "Revenue Lab → действия CEO",
            "headline_ru": scan["headline_ru"],
            "ceo_actions": scan["ceo_actions"][:8],
            "findings": scan["findings"],
            "recent_alerts": self._read_jsonl(self._alerts, limit=10),
            "rule_ru": scan["rule_ru"],
        }

    def _append(self, path: Path, row: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _read_jsonl(self, path: Path, *, limit: int) -> list[dict[str, Any]]:
        if not path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").strip().splitlines()[-limit:]:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return list(reversed(rows))
