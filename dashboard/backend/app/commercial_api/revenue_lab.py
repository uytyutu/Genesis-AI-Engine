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
        "env_any_enough": ["STRIPE_SECRET_KEY"],
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
        "next_use_title_ru": "Используй Stripe: первая реальная оплата",
        "next_use_ru": (
            "Ключ уже есть. Следующий шаг — провести первую клиентскую оплату "
            "(сайт / Path A / API-пакет) → webhook → CONFIRMED в Ledger. "
            "Пока нет оплаты — Stripe остаётся Candidate (ключ ≠ деньги)."
        ),
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
        "next_use_title_ru": "Продай Audit API первому клиенту",
        "next_use_ru": (
            "Gateway готов. Создай ключ Starter, дай клиенту POST /api/v1/audit — "
            "доход только после prepaid/оплаты пакета, не от симуляции."
        ),
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
        "ceo_action_ru": "Зарегистрируй publisher на Awin → вставь AWIN_API_TOKEN + AWIN_PUBLISHER_ID",
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
        "env_aliases": {"DIGISTORE24_API_KEY": ["DIGISTORE_API_KEY"]},
        "api_ok": True,
        "automation_allowed": True,
        "payouts": True,
        "model_ru": "IPN/API учёта конверсий → комиссия",
        "ceo_action_ru": "Создай аккаунт Digistore24 → DIGISTORE24_API_KEY в .env.local → перезапуск Genesis",
        "income_hypothesis_ru": (
            "Цифровые продукты + партнёрская ссылка после аудита сайта клиента. "
            "Выплата после подтверждённой продажи."
        ),
        "priority": 4,
        "uses_farm": True,
        "uses_commercial_api": False,
        "next_use_title_ru": "Используй Digistore24: легальные возможности дохода",
        "next_use_ru": (
            "Ключ уже настроен — не просим добавить снова. "
            "Следующая задача Lab/фермы: официальный API Digistore24 "
            "(статистика, комиссии, продажи) + рекомендации продуктов после аудита клиента. "
            "Доход в отчётах — только после первой CONFIRMED комиссии. "
            "Без обхода ToS и без симуляции выплат."
        ),
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
        "next_use_title_ru": "Выбери нишу отчёта под Stripe/API",
        "next_use_ru": (
            "Ищи доход от уже доступных контуров (ферма + Stripe + Audit API): "
            "отчёт клиенту за деньги, не «бесплатный data API = доход»."
        ),
    },
)


def _env_ok(names: list[str]) -> bool:
    if not names:
        return True
    return all(bool(os.getenv(n, "").strip()) for n in names)


def _env_any(names: list[str]) -> bool:
    return any(bool(os.getenv(n, "").strip()) for n in names)


def _missing_env(names: list[str]) -> list[str]:
    return [n for n in names if not os.getenv(n, "").strip()]


def _seed_connected(seed: dict[str, Any]) -> tuple[bool, list[str]]:
    """Return (keys_ok, missing_required_names). Aliases and env_any_enough supported."""
    required = list(seed.get("env_vars") or [])
    aliases: dict[str, list[str]] = dict(seed.get("env_aliases") or {})
    any_enough = list(seed.get("env_any_enough") or [])

    if any_enough:
        if _env_any(any_enough):
            missing = _missing_env(required)
            return True, missing  # connected enough; missing = optional leftovers (e.g. webhook)
        return False, _missing_env(any_enough)

    if not required:
        return True, []

    missing: list[str] = []
    for name in required:
        alts = [name, *aliases.get(name, [])]
        if not _env_any(alts):
            missing.append(name)
    return (len(missing) == 0), missing


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
            connected, missing = _seed_connected(seed)
            status = "ready" if connected else "needs_ceo"
            if connected and missing:
                status_ru = f"Ключи есть · ещё нужно: {', '.join(missing)}"
            elif connected:
                status_ru = "Ключи на месте"
            else:
                status_ru = "Нужен аккаунт / ключ CEO"
            finding = {
                "id": seed["id"],
                "name": seed["name"],
                "type": seed["type"],
                "api": seed["api_ok"],
                "automation_allowed": seed["automation_allowed"],
                "payouts": seed["payouts"],
                "connected": connected,
                "missing_env": missing,
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
                    "CONFIRMED только после реальной выплаты/оплаты. "
                    "Скан не ищет интернет — это фиксированный список кандидатов."
                ),
            }
            findings.append(finding)
            if not connected:
                action = {
                    "id": f"act-{seed['id']}",
                    "priority": seed["priority"],
                    "source_id": seed["id"],
                    "kind": "connect_key",
                    "title_ru": f"Подключи: {seed['name']}",
                    "action_ru": seed["ceo_action_ru"],
                    "why_income_ru": seed["income_hypothesis_ru"],
                    "env_vars": seed.get("env_vars") or [],
                    "missing_env": missing,
                    "at": _now(),
                }
                ceo_actions.append(action)
                if persist_alerts:
                    self._append(self._alerts, action)
            elif missing:
                # Partial: e.g. Stripe secret ok, webhook still needed
                action = {
                    "id": f"act-{seed['id']}-partial",
                    "priority": int(seed["priority"]) + 50,
                    "source_id": seed["id"],
                    "kind": "complete_keys",
                    "title_ru": f"Дополни: {seed['name']}",
                    "action_ru": f"Добавь в .env.local: {', '.join(missing)} → перезапуск Genesis",
                    "why_income_ru": seed["income_hypothesis_ru"],
                    "env_vars": missing,
                    "missing_env": missing,
                    "at": _now(),
                }
                ceo_actions.append(action)
            elif seed.get("next_use_ru"):
                # Key already present — never ask to add the same key again.
                action = {
                    "id": f"act-{seed['id']}-use",
                    "priority": 20 + int(seed.get("priority") or 99),
                    "source_id": seed["id"],
                    "kind": "use_connected",
                    "title_ru": seed.get("next_use_title_ru")
                    or f"Используй: {seed['name']}",
                    "action_ru": seed["next_use_ru"],
                    "why_income_ru": (
                        "Ключ есть ≠ доход. Следующий шаг — легально использовать уже "
                        "подключённый API/ферму до первой CONFIRMED операции."
                    ),
                    "env_vars": [],
                    "missing_env": [],
                    "at": _now(),
                }
                ceo_actions.append(action)

        # Never ask to reconnect Digistore/Stripe/etc when keys are present.
        ceo_actions = [
            a
            for a in ceo_actions
            if not (
                a.get("kind") == "connect_key"
                and any(
                    f["id"] == a.get("source_id") and f.get("connected")
                    for f in findings
                )
            )
        ]

        ceo_actions.sort(key=lambda a: int(a.get("priority") or 99))
        digistore_use = next(
            (
                a
                for a in ceo_actions
                if a.get("source_id") == "digistore24_affiliate"
                and a.get("kind") == "use_connected"
            ),
            None,
        )
        top = ceo_actions[0] if ceo_actions else None
        if digistore_use:
            # Digistore key done → headline pushes next legitimate use, not "add key again".
            headline = digistore_use["title_ru"] + " — " + digistore_use["action_ru"]
        elif top:
            headline = top["title_ru"] + " — " + top.get("why_income_ru", top.get("action_ru", ""))
        else:
            headline = (
                "Все известные кандидаты с ключами закрыты — "
                "ищи доход через уже подключённые API и ферму до первой CONFIRMED операции."
            )

        return {
            "ok": True,
            "scanned_at": _now(),
            "findings": findings,
            "ceo_actions": ceo_actions,
            "headline_ru": headline,
            "rule_ru": (
                "Lab не создаёт аккаунты и не принимает ToS. "
                "Ключ есть ≠ деньги (Reality over Simulation). "
                "Если ключ уже в .env.local — Lab не просит его снова; "
                "следующий шаг = легально использовать API/ферму."
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
