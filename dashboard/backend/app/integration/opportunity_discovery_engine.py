"""Opportunity Discovery — ищет возможности, не деньги. Деньги — после сделки.

Legal gate → Win Probability → Cost Engine → CEO выбирает → конвейер.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.integration.production_platform import (
    CAPABILITY_MARKETPLACE,
    PRODUCT_CATALOG,
    cost_engine_quote,
)

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_LEGAL_SOURCES = frozenset(
    {"asset_scan", "manual", "inbound_chat", "google_maps", "google_business"}
)

_FORBIDDEN_OPPORTUNITY_TYPES = frozenset({"exploit", "pentest"})

_LOST_REASON_CODES: dict[str, str] = {
    "expensive": "Дорого",
    "has_contractor": "Уже есть подрядчик",
    "not_relevant": "Неактуально",
    "no_budget": "Нет бюджета",
    "no_response": "Нет ответа",
    "other": "Другое",
}

_ISSUE_SERVICE_RULES: list[tuple[str, str, str]] = [
    ("kategorie", "svc_catalog", "Категоризация каталога"),
    ("katalog", "svc_catalog", "Категоризация каталога"),
    ("produkt", "svc_catalog", "Категоризация товаров"),
    ("seo", "svc_catalog", "SEO и структура каталога"),
    ("seitentitel", "svc_catalog", "SEO метаданные"),
    ("social-meta", "svc_catalog", "Social preview / метаданные"),
    ("inhalt", "svc_document_labeling", "Структурирование контента"),
    ("pdf", "svc_document_labeling", "Разметка документов"),
    ("ocr", "svc_ocr", "OCR + структурирование"),
    ("übersetz", "svc_translation_qa", "Translation QA"),
    ("translation", "svc_translation_qa", "Translation QA"),
    ("duplikat", "svc_data_qa", "Проверка качества данных"),
    ("qualität", "svc_data_qa", "QA датасета"),
    ("https", "svc_data_qa", "QA публичных данных"),
    ("langsame", "svc_data_qa", "QA производительности"),
]

_METHODS_RU: list[dict[str, str]] = [
    {
        "id": "resource_arbitrage",
        "title_ru": "Арбитраж ресурсов",
        "summary_ru": "ИИ за копейки → B2B-отчёт по рыночной цене. Cost Engine показывает маржу.",
        "status_ru": "Активен",
    },
    {
        "id": "adaptive_b2b",
        "title_ru": "Партизанский B2B",
        "summary_ru": "Без платной рекламы — готовое предложение под проблему клиента.",
        "status_ru": "Активен",
    },
    {
        "id": "crash_test",
        "title_ru": "Crash-Test Toloka",
        "summary_ru": "Биржа = тренажёр конвейера, не центр стратегии.",
        "status_ru": "Активен",
    },
    {
        "id": "truth_armor",
        "title_ru": "Truth Engine",
        "summary_ru": "Продаём проверку качества — меньше споров об оплате.",
        "status_ru": "Активен",
    },
]

_CTO_WARNING_RU = (
    "Осторожно: мульти-акки и обход лимитов бирж запрещены. "
    "Системный метод = реальная проблема + наше решение, не «где урвать»."
)

_MISSION_FORMULA_RU = [
    "Обнаружить проблему",
    "Оценить её",
    "Подготовить предложение",
    "Получить заказ",
    "Выполнить работу",
    "Проверить качество",
    "Получить оплату",
    "Запомнить опыт",
    "Следующий заказ — лучше",
]


def _lost_reasons_path(memory_dir: Path) -> Path:
    return memory_dir / "lost_reasons.jsonl"


def load_lost_reasons(memory_dir: Path | None = None) -> list[dict[str, Any]]:
    path = _lost_reasons_path(memory_dir or _DEFAULT_MEMORY)
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def record_lost_reason(
    *,
    opportunity_id: str,
    reason_code: str,
    company_name: str = "",
    note_ru: str = "",
    memory_dir: Path | None = None,
) -> dict[str, Any]:
    code = reason_code if reason_code in _LOST_REASON_CODES else "other"
    entry = {
        "opportunity_id": opportunity_id,
        "company_name": company_name,
        "reason_code": code,
        "reason_ru": _LOST_REASON_CODES[code],
        "note_ru": (note_ru or "")[:300],
        "at": datetime.now(timezone.utc).isoformat(),
    }
    mem = memory_dir or _DEFAULT_MEMORY
    path = _lost_reasons_path(mem)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def lost_reason_database(memory_dir: Path | None = None) -> dict[str, Any]:
    rows = load_lost_reasons(memory_dir)
    by_code: dict[str, int] = {}
    for r in rows:
        code = str(r.get("reason_code") or "other")
        by_code[code] = by_code.get(code, 0) + 1
    top = sorted(by_code.items(), key=lambda x: -x[1])[:5]
    return {
        "title_ru": "База причин отказов",
        "hint_ru": "При отказе укажите причину — система учится, какие офферы не работают.",
        "total": len(rows),
        "by_reason": [
            {"code": c, "label_ru": _LOST_REASON_CODES.get(c, c), "count": n} for c, n in top
        ],
        "reason_options": [{"code": k, "label_ru": v} for k, v in _LOST_REASON_CODES.items()],
        "recent": rows[-5:][::-1],
    }


def _domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def _issue_texts(row: dict[str, Any]) -> list[str]:
    analysis = row.get("site_analysis") if isinstance(row.get("site_analysis"), dict) else {}
    issues = list(analysis.get("issues") or [])
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    if meta.get("issues"):
        issues.extend(meta.get("issues") or [])
    return [str(i) for i in issues if str(i).strip()]


def _pick_service(issues: list[str], issue_count: int) -> tuple[str, str, float]:
    joined = " ".join(i.lower() for i in issues)
    for needle, svc_id, label in _ISSUE_SERVICE_RULES:
        if needle in joined:
            if svc_id == "svc_catalog":
                return svc_id, label, max(10_000.0, issue_count * 2_500.0)
            if svc_id in ("svc_document_labeling", "svc_ocr"):
                return svc_id, label, max(500.0, issue_count * 200.0)
            return svc_id, label, max(5_000.0, issue_count * 1_000.0)
    if issue_count >= 4:
        return "svc_data_qa", "Проверка качества данных", max(10_000.0, issue_count * 2_000.0)
    if issue_count >= 2:
        return "svc_catalog", "Категоризация / SEO", max(10_000.0, issue_count * 1_500.0)
    return "svc_data_qa", "Проверка качества данных", max(1_000.0, issue_count * 500.0)


def _legal_gate(row: dict[str, Any]) -> dict[str, Any]:
    source = str(row.get("source_id") or "")
    opp_type = str(row.get("opportunity_type") or "")
    url = str(row.get("website_url") or "")
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    hunter = meta.get("hunter_scenarios") if isinstance(meta.get("hunter_scenarios"), dict) else {}

    legal = source in _LEGAL_SOURCES and opp_type not in _FORBIDDEN_OPPORTUNITY_TYPES
    if url and not url.startswith(("http://", "https://")):
        legal = False
    if int(hunter.get("bounty") or 0) > 0 and not meta.get("official_bounty_program"):
        legal = False

    return {
        "legal": legal,
        "note_ru": "Только публичные данные · CEO решает · без автопродаж",
    }


def _market_memory(rows: list[dict[str, Any]], row: dict[str, Any]) -> dict[str, Any]:
    domain = _domain(str(row.get("website_url") or ""))
    company = str(row.get("company_name") or "").strip().lower()
    prior_lost = 0
    prior_won = 0
    last_reason: str | None = None
    for other in rows:
        if other.get("id") == row.get("id"):
            continue
        same = (domain and _domain(str(other.get("website_url") or "")) == domain) or (
            company and str(other.get("company_name") or "").strip().lower() == company
        )
        if not same:
            continue
        if other.get("status") == "lost":
            prior_lost += 1
            meta = other.get("meta") if isinstance(other.get("meta"), dict) else {}
            last_reason = str(meta.get("lost_reason_ru") or other.get("notes") or "отказ")[:120]
        if other.get("status") == "won":
            prior_won += 1
    return {
        "prior_lost": prior_lost,
        "prior_won": prior_won,
        "last_lost_reason_ru": last_reason,
        "score_penalty": min(25, prior_lost * 12),
    }


def _similar_wins(all_rows: list[dict[str, Any]], service_id: str) -> int:
    return sum(
        1
        for r in all_rows
        if r.get("status") == "won" and str(r.get("recommended_package_id") or "") == service_id
    )


def _win_probability(
    row: dict[str, Any],
    *,
    issues: list[str],
    issue_count: int,
    quote: dict[str, Any] | None,
    memory: dict[str, Any],
    all_rows: list[dict[str, Any]],
    service_id: str,
) -> tuple[int, list[str]]:
    """Win Probability % with explainable reasons."""
    pct = 42
    reasons: list[str] = []

    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    analysis = row.get("site_analysis") if isinstance(row.get("site_analysis"), dict) else {}

    if issue_count >= 3:
        pct += 12
        reasons.append(f"На сайте {issue_count} проблем — видимая потребность в услуге")
    if meta.get("abandoned") or any("veraltet" in i.lower() or "baustelle" in i.lower() for i in issues):
        pct += 8
        reasons.append("Сайт давно не обновлялся — выше шанс, что примут помощь")
    if any("kontakt" in i.lower() for i in issues):
        pct -= 12
        reasons.append("Нет контактов на сайте — сложнее выйти на ЛПР")
    else:
        pct += 5
        reasons.append("Контактная форма найдена — проще начать диалог")

    if quote and quote.get("ok"):
        price = float(quote.get("sell_price_eur") or 0)
        minutes = int(quote.get("duration_minutes") or 999)
        if price <= 300:
            pct += 10
            reasons.append(f"Цена {price:.0f} € — в зоне «до 300 €», по статистике чаще покупают")
        elif price > 500:
            pct -= 8
            reasons.append(f"Цена {price:.0f} € — выше типичного порога для холодного оффера")
        if minutes < 1440:
            pct += 8
            reasons.append(f"Срок {quote.get('duration_label_ru')} — быстрее суток, проще согласовать")
        reasons.append("В предложение включён Truth Engine QA-отчёт бесплатно")

    wins = _similar_wins(all_rows, service_id)
    if wins >= 1:
        pct += min(15, wins * 5)
        reasons.append(f"Похожие компании уже покупали эту услугу ({wins} побед в журнале)")

    if int(memory.get("prior_lost") or 0) > 0:
        pct -= 18
        reasons.append("Был отказ ранее — снизили вероятность")
    if int(memory.get("prior_won") or 0) > 0:
        pct += 20
        reasons.append("Уже была успешная сделка с этой компанией")

    imp = analysis.get("improvement_score")
    if imp is not None and int(imp) >= 40:
        pct += 5
        reasons.append("Размер проблемы соответствует нашему пакету услуг")

    pct = max(5, min(92, pct))
    return pct, reasons[:6]


def _opportunity_score(legal: bool, memory_penalty: int, issue_count: int, win_pct: int) -> int:
    base = win_pct
    if issue_count >= 3:
        base += 5
    if not legal:
        base = min(base, 15)
    base -= memory_penalty
    return max(0, min(100, base))


def build_success_patterns(
    opportunities: list[dict[str, Any]],
    *,
    memory_dir: Path | None = None,
) -> dict[str, Any]:
    """Аналитика: что работало в выигранных сделках."""
    won = [r for r in opportunities if r.get("status") == "won"]
    lost = [r for r in opportunities if r.get("status") == "lost"]
    proposed = [r for r in opportunities if r.get("status") in ("proposed", "contacted", "qualified")]

    def _price(r: dict) -> float:
        return float(r.get("recommended_price_eur") or r.get("potential_value_eur") or 0)

    won_under_300 = sum(1 for r in won if _price(r) <= 300 or _price(r) == 0)
    patterns: list[dict[str, str]] = []

    if won:
        if won_under_300 >= max(1, len(won) // 2):
            patterns.append(
                {
                    "pattern_ru": "Цена до 300 €",
                    "insight_ru": f"Из {len(won)} побед — {won_under_300} с ценой ≤300 €",
                    "action_hint_ru": "Держите холодные офферы в этом диапазоне",
                }
            )
        patterns.append(
            {
                "pattern_ru": "QA-отчёт в комплекте",
                "insight_ru": "Победители получали Truth Engine отчёт — меньше споров",
                "action_hint_ru": "Всегда упоминайте отчёт проверки в КП",
            }
        )
    else:
        patterns.append(
            {
                "pattern_ru": "Пока нет побед",
                "insight_ru": f"В журнале {len(proposed)} в работе, {len(lost)} отказов",
                "action_hint_ru": "Отмечайте причины отказов — появятся реальные паттерны",
            }
        )

    lost_db = lost_reason_database(memory_dir)
    if lost_db["by_reason"]:
        top = lost_db["by_reason"][0]
        patterns.append(
            {
                "pattern_ru": f"Частый отказ: {top['label_ru']}",
                "insight_ru": f"{top['count']} раз в базе причин",
                "action_hint_ru": "Корректируйте цену или оффер под эту причину",
            }
        )

    return {
        "title_ru": "Паттерны успеха",
        "hint_ru": "Из реальных сделок и отказов — не из теории. Чем больше данных, тем точнее.",
        "won_count": len(won),
        "lost_count": len(lost),
        "proposed_count": len(proposed),
        "patterns": patterns,
    }


def evaluate_opportunity(
    row: dict[str, Any],
    *,
    all_rows: list[dict[str, Any]] | None = None,
    workers: int = 10,
) -> dict[str, Any]:
    legal = _legal_gate(row)
    memory = _market_memory(all_rows or [], row)
    issues = _issue_texts(row)
    issue_count = len(issues)
    analysis = row.get("site_analysis") if isinstance(row.get("site_analysis"), dict) else {}

    svc_id, svc_label, volume = _pick_service(issues, issue_count)
    quote = cost_engine_quote(service_id=svc_id, volume=volume, workers=workers) if legal["legal"] else None

    win_pct, win_reasons = _win_probability(
        row,
        issues=issues,
        issue_count=issue_count,
        quote=quote if quote and quote.get("ok") else None,
        memory=memory,
        all_rows=all_rows or [],
        service_id=svc_id,
    )
    score = _opportunity_score(legal["legal"], int(memory.get("score_penalty") or 0), issue_count, win_pct)

    primary_problem = issues[0][:80] if issues else svc_label

    return {
        "opportunity_id": row.get("id"),
        "company_name": row.get("company_name") or "—",
        "website_url": row.get("website_url") or "",
        "status": row.get("status"),
        "legal_gate": legal,
        "primary_problem_ru": primary_problem,
        "problems_count": issue_count,
        "problems_preview_ru": issues[:5],
        "service_id": svc_id,
        "service_label_ru": svc_label,
        "opportunity_score_pct": score,
        "win_probability_pct": win_pct,
        "win_probability_reasons_ru": win_reasons,
        "sell_price_eur": float(quote.get("sell_price_eur") or 0) if quote and quote.get("ok") else 0,
        "duration_label_ru": quote.get("duration_label_ru") if quote else None,
        "margin_pct": float(quote.get("margin_pct") or 0) if quote and quote.get("ok") else 0,
        "market_memory": memory,
        "proposal_ready": bool(legal["legal"] and quote and quote.get("ok") and win_pct >= 35),
        "truth_kind": "ESTIMATE",
        "business_monitor_ru": {
            "site_stale": any("veraltet" in i.lower() for i in issues),
            "seo_weak": any("seo" in i.lower() or "titel" in i.lower() for i in issues),
            "no_contact": any("kontakt" in i.lower() for i in issues),
            "improvement_score": analysis.get("improvement_score"),
        },
    }


def _proposal_draft(row: dict[str, Any], *, service_title: str, quote: dict[str, Any], issues: list[str]) -> str:
    company = row.get("company_name") or "компания"
    issues_block = "\n".join(f"• {i}" for i in issues[:6]) or "• Проблемы качества публичных данных"
    return (
        f"Коммерческое предложение · {company}\n\n"
        f"Обнаруженные проблемы:\n{issues_block}\n\n"
        f"Услуга: {service_title}\n"
        f"Срок: ~{quote.get('duration_label_ru', '—')}\n"
        f"Стоимость: {quote.get('sell_price_eur', 0):.2f} €\n"
        f"В комплекте: Truth Engine QA-отчёт + {', '.join(quote.get('deliverables_ru') or ['JSON', 'CSV'])}\n\n"
        f"Фиксированная цена до старта. Деньги — после принятия результата."
    )


def build_opportunity_discovery(
    opportunities: list[dict[str, Any]],
    *,
    farm_state: dict[str, Any] | None = None,
    toloka_verdict: str = "",
    workers: int = 10,
    memory_dir: Path | None = None,
) -> dict[str, Any]:
    mem = memory_dir or _DEFAULT_MEMORY
    state = farm_state or {}
    labels = int(state.get("labels_export_count") or 0)

    evaluated: list[dict[str, Any]] = []
    for row in opportunities:
        if row.get("status") in ("won", "lost"):
            continue
        ev = evaluate_opportunity(row, all_rows=opportunities, workers=workers)
        if ev["legal_gate"]["legal"] or ev["problems_count"] > 0:
            evaluated.append(ev)

    evaluated.sort(key=lambda x: int(x.get("win_probability_pct") or 0), reverse=True)
    top = evaluated[:12]
    pipeline_value = round(sum(float(e.get("sell_price_eur") or 0) for e in top[:5]), 2)

    return {
        "engine_id": "opportunity_discovery",
        "title_ru": "Обнаружение возможностей",
        "subtitle_ru": "Ищем проблемы бизнеса, не деньги. Деньги — после сделки.",
        "tagline_ru": "Opportunity Discovery · системный метод, не «где урвать»",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "toloka_hint_ru": toloka_verdict or "Toloka = тренажёр · B2B = основной путь",
        "mission_formula_ru": _MISSION_FORMULA_RU,
        "methods": _METHODS_RU,
        "cto_warning_ru": _CTO_WARNING_RU,
        "ceo_hints_ru": [
            "1. Запустите ферму (feed) — Spider найдёт компании с проблемами",
            "2. Смотрите Win Probability и «почему именно N%»",
            "3. «Подготовить предложение» — черновик КП, вы отправляете сами",
            "4. При отказе — укажите причину (база учится)",
            "5. Паттерны успеха обновляются после каждой сделки",
        ],
        "stats": {
            "scanned": len(opportunities),
            "evaluated": len(evaluated),
            "high_win_probability": sum(1 for e in evaluated if int(e.get("win_probability_pct") or 0) >= 55),
            "pipeline_value_eur": pipeline_value,
            "labels_export_count": labels,
        },
        "workflow_ru": _MISSION_FORMULA_RU,
        "top_opportunities": top,
        "lost_reason_database": lost_reason_database(mem),
        "success_patterns": build_success_patterns(opportunities, memory_dir=mem),
        "automation_level_ru": (
            "Авто: скан, Win Probability, цена, черновик. "
            "Вручную: отправка, переговоры, оплата."
        ),
    }


def prepare_commercial_proposal(
    row: dict[str, Any],
    *,
    all_rows: list[dict[str, Any]] | None = None,
    workers: int = 10,
) -> dict[str, Any]:
    ev = evaluate_opportunity(row, all_rows=all_rows, workers=workers)
    if not ev["legal_gate"]["legal"]:
        return {"ok": False, "message_ru": "Нельзя готовить предложение — не прошёл legal gate", "evaluation": ev}
    quote = cost_engine_quote(
        service_id=ev["service_id"],
        volume=max(1000, ev["problems_count"] * 1000),
        workers=workers,
    )
    if not quote.get("ok"):
        return {"ok": False, "message_ru": "Не удалось рассчитать цену", "evaluation": ev}

    draft = _proposal_draft(
        row,
        service_title=str(ev.get("service_label_ru") or ""),
        quote=quote,
        issues=ev.get("problems_preview_ru") or [],
    )
    return {
        "ok": True,
        "opportunity_id": row.get("id"),
        "proposal_ru": draft,
        "recommended_package_id": ev.get("service_id"),
        "recommended_price_eur": ev.get("sell_price_eur"),
        "win_probability_pct": ev.get("win_probability_pct"),
        "evaluation": ev,
        "truth_kind": "ESTIMATE",
    }


# Backward-compatible aliases (internal)
build_revenue_discovery = build_opportunity_discovery
