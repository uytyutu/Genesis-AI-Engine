"""Explainability v0 — deterministic «почему» для VRE / CHANNEL_REVIEW (no LLM)."""

from __future__ import annotations

from typing import Any


def explain_vre_verdict(
    *,
    verdict: str,
    vre_gate: dict[str, Any],
    toloka_status: dict[str, Any],
    error_ledger_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    vre_level = int(vre_gate.get("vre_level") or 0)
    confidence = vre_gate.get("revenue_confidence") or {}
    conf_pct = int(confidence.get("confidence_pct") or 0)
    psc = int(toloka_status.get("pipeline_success_count") or 0)
    wallet = bool((vre_gate.get("vre") or {}).get("level", 0) >= 2)
    channel_review = bool(vre_gate.get("channel_review_required"))

    if verdict == "CHANNEL_REVIEW" or channel_review:
        return {
            "title_ru": "Почему CHANNEL_REVIEW",
            "recommendation_ru": "Сменить канал монетизации — не писать код",
            "reasons": [
                f"{psc} успешных pipeline run (FACT)",
                "wallet = 0 (нет CEO_CONFIRMATION)",
                f"Revenue Confidence {conf_pct}% (ESTIMATE — деньги не подтверждены)",
            ],
            "probabilities": {
                "code_bug": "низкая",
                "monetization_model": "высокая",
                "label_quality": _label_quality_prob(error_ledger_summary),
            },
            "next_action_ru": vre_gate.get("ceo_action_now") or "Toloka support / другой канал (HIT, Scale, B2B)",
        }

    if verdict == "PASS" or vre_level >= 4:
        return {
            "title_ru": "Почему VRE PASS",
            "recommendation_ru": "Mission 1 Freeze можно снимать — выбрать один Force Vector",
            "reasons": [
                f"VRE LEVEL {vre_level}",
                "Цикл повторяем (wallet + withdraw + pipeline)",
            ],
            "probabilities": {},
            "next_action_ru": "Truth Engine → Decision Memory → Anti-Fragility (roadmap CEO)",
        }

    if verdict == "COMMERCIAL_GATE":
        return {
            "title_ru": "Почему COMMERCIAL_GATE",
            "recommendation_ru": "Техника закрыта — проверь wallet Toloka вручную",
            "reasons": [
                "Pipeline / submit OK (FACT)",
                "Wallet не подтверждён CEO",
            ],
            "probabilities": {
                "code_bug": "низкая",
                "monetization_model": "средняя",
                "label_quality": _label_quality_prob(error_ledger_summary),
            },
            "next_action_ru": "48ч без кода · platform.toloka.ai → Wallet",
        }

    if error_ledger_summary and error_ledger_summary.get("by_taxonomy", {}).get("format", 0) >= 2:
        return {
            "title_ru": "Почему застряли на submit",
            "recommendation_ru": "Исправить формат export — Error Ledger показывает format",
            "reasons": ["Повтор reject format в Error Ledger"],
            "probabilities": {"code_bug": "средняя", "monetization_model": "низкая", "label_quality": "низкая"},
            "next_action_ru": error_ledger_summary.get("hint_ru") or "Проверь DATASET_FIELDS",
        }

    return {
        "title_ru": f"Почему {verdict}",
        "recommendation_ru": vre_gate.get("headline") or "Продолжить конвейер",
        "reasons": [vre_gate.get("core_question") or ""],
        "probabilities": {},
        "next_action_ru": vre_gate.get("ceo_action_now") or "feed + tick + submit",
    }


def _label_quality_prob(error_ledger_summary: dict[str, Any] | None) -> str:
    if not error_ledger_summary:
        return "неизвестна"
    content = int((error_ledger_summary.get("by_taxonomy") or {}).get("content", 0))
    if content >= 2:
        return "высокая"
    if content >= 1:
        return "средняя"
    return "низкая"
