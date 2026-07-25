"""Digistore24 — official API capability brief for Revenue Lab.

Facts from Digistore24 developer docs (API basics, function reference).
Does not invent earnings. Does not call Digistore live unless a later probe is added.
Reality over Simulation: API key ≠ commission ≠ Ledger income.
"""

from __future__ import annotations

from typing import Any

# Official HTTP base (Digistore24 API basics)
API_BASE = "https://www.digistore24.com/api/call/{FUNCTION}"
AUTH_HEADER = "X-DS-API-KEY"
DOCS_URL = "https://dev.digistore24.com/hc/en-us/articles/32479630493585-API-basics"

MONEY_CHAIN_RU: tuple[str, ...] = (
    "Ключ API",
    "Доступ к данным",
    "Рабочий процесс (Virtus / ферма / CEO)",
    "Клиент переходит по партнёрской / promo-ссылке",
    "Продажа на Digistore24",
    "CONFIRMED комиссия у Digistore24",
    "Запись в Virtus Ledger",
    "Реальный доход",
)


def digistore24_capability_brief(*, key_present: bool) -> dict[str, Any]:
    """Answer Lab's three Digistore questions — capability only, no fake €."""
    q1 = {
        "question_ru": "Что позволяет официальный API?",
        "answers": [
            {
                "capability": "Статистика",
                "ok": True,
                "detail_ru": (
                    "Да: statsSales, statsSalesSummary, statsDailyAmounts, "
                    "statsExpectedPayouts, statsMarketplace, statsAffiliateToplist "
                    "(доступ зависит от прав ключа)."
                ),
                "api_refs": [
                    "statsSales",
                    "statsSalesSummary",
                    "statsDailyAmounts",
                    "statsExpectedPayouts",
                ],
            },
            {
                "capability": "Продажи",
                "ok": True,
                "detail_ru": (
                    "Да: чтение продаж/статистики и связанных данных заказов "
                    "(readonly). Изменение заказов — только writable-ключ."
                ),
                "api_refs": ["statsSales", "listCommissions"],
            },
            {
                "capability": "Партнёрские / promo-ссылки",
                "ok": True,
                "detail_ru": (
                    "Да, как часть платформы: продукт + параметры affiliate "
                    "(например aff / cam в URL заказа) и связанные tracking-функции "
                    "(renderJsTrackingCode). Это не «магическая генерация денег»."
                ),
                "api_refs": ["listProducts", "renderJsTrackingCode", "createBuyUrl"],
            },
            {
                "capability": "Комиссии",
                "ok": True,
                "detail_ru": (
                    "Да: listCommissions (и связанные commission-функции) — "
                    "чтение начислений. Деньги в Virtus появляются только после "
                    "реальной комиссии и проводки в Ledger."
                ),
                "api_refs": ["listCommissions"],
            },
            {
                "capability": "Клики / сырой трафик",
                "ok": False,
                "detail_ru": (
                    "Публичный API не заменяет полный click-stream. "
                    "Не строить отчёт «клики → €» только из API без факта продажи."
                ),
                "api_refs": [],
            },
        ],
        "auth_ru": (
            f"Ключ в заголовке {AUTH_HEADER}. Вызов: {API_BASE}. "
            "Права ключа: readonly | writable | developer (см. API basics)."
        ),
        "docs_url": DOCS_URL,
    }

    q2 = {
        "question_ru": "Какие действия можно автоматизировать официально?",
        "actions": [
            {
                "id": "read_stats",
                "title_ru": "Считать статистику продаж и ожидаемые выплаты",
                "official": True,
                "leads_to_first_commission": False,
                "note_ru": "Даёт обзор. Само по себе комиссию не создаёт.",
            },
            {
                "id": "read_commissions",
                "title_ru": "Читать список комиссий (listCommissions)",
                "official": True,
                "leads_to_first_commission": False,
                "note_ru": "Показывает уже случившиеся начисления — не создаёт новые.",
            },
            {
                "id": "list_products",
                "title_ru": "Список продуктов (listProducts) для рекомендаций",
                "official": True,
                "leads_to_first_commission": "enables",
                "note_ru": (
                    "Нужно, чтобы ферма/аудит предложила релевантный продукт "
                    "с корректной promo/affiliate-ссылкой."
                ),
            },
            {
                "id": "promo_links",
                "title_ru": "Формировать / отдавать партнёрские или buy-URL",
                "official": True,
                "leads_to_first_commission": "enables",
                "note_ru": (
                    "Официальный путь к клику клиента. Без перехода и продажи — 0 €."
                ),
            },
            {
                "id": "reports_alerts",
                "title_ru": "Отчёты и уведомления CEO о новых комиссиях/платежах",
                "official": True,
                "leads_to_first_commission": False,
                "note_ru": (
                    "IPN/watch payment + опрос API. Контроль Reality — не симуляция дохода."
                ),
            },
            {
                "id": "fake_farm_ticks",
                "title_ru": "Симулировать комиссии локальными тиками фермы",
                "official": False,
                "leads_to_first_commission": False,
                "note_ru": "Запрещено как доход (Reality over Simulation).",
            },
        ],
    }

    q3 = {
        "question_ru": "Что реально может привести к первой комиссии?",
        "must_happen_ru": [
            "Клиент получает ценность от Virtus (аудит / сайт / рекомендация).",
            "Ему дают официальную Digistore promo/affiliate-ссылку на подходящий продукт.",
            "Клиент переходит и покупает на Digistore24.",
            "Digistore начисляет комиссию партнёру.",
            "Virtus фиксирует CONFIRMED только после подтверждённой комиссии/выплаты — не от ключа.",
        ],
        "api_role_ru": (
            "API автоматизирует доступ к продуктам, ссылкам, статистике и факту комиссии. "
            "API сам по себе деньги не печатает."
        ),
        "first_euro_path": [
            {
                "step": 1,
                "title_ru": "Проверить ключ (ping / getUserInfo)",
                "creates_money": False,
            },
            {
                "step": 2,
                "title_ru": "listProducts → подобрать продукт под аудит клиента",
                "creates_money": False,
            },
            {
                "step": 3,
                "title_ru": "Выдать официальную партнёрскую / promo-ссылку в рабочем процессе",
                "creates_money": False,
            },
            {
                "step": 4,
                "title_ru": "Клиент покупает → listCommissions / IPN видит комиссию",
                "creates_money": True,
            },
            {
                "step": 5,
                "title_ru": "Только тогда → Ledger CONFIRMED → реальный доход",
                "creates_money": True,
            },
        ],
        "verdict_ru": (
            "Первая комиссия = реальная продажа через вашу ссылку, не «успешный API-вызов»."
        ),
    }

    return {
        "id": "digistore24",
        "title_ru": "Digistore24 · ответы Revenue Lab",
        "key_present": bool(key_present),
        "status_ru": (
            "Ключ есть — можно строить рабочий процесс. Active/доход — только после CONFIRMED комиссии."
            if key_present
            else "Ключа нет — сначала DIGISTORE24_API_KEY в .env.local → перезапуск Genesis."
        ),
        "reality_chain_ru": list(MONEY_CHAIN_RU),
        "reality_law_id": "FINANCE_REALITY_OVER_SIMULATION",
        "q1_api_allows": q1,
        "q2_automatable": q2,
        "q3_first_commission": q3,
        "next_lab_task_ru": (
            "Не просить ключ снова. Следующая задача: "
            "(1) probe getUserInfo/ping, "
            "(2) listProducts под нишу клиента, "
            "(3) встроить выдачу официальной ссылки в путь после аудита, "
            "(4) читать listCommissions → только факт → Ledger."
            if key_present
            else "Сначала ключ CEO, затем этот же план."
        ),
        "sources_ru": (
            "Digistore24 API basics + function reference (listProducts, listCommissions, "
            "statsSales*, getUserInfo, createBuyUrl / tracking). "
            "Virtus не обходит ToS."
        ),
    }
