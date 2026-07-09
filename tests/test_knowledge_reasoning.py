"""Tests — Knowledge Reasoning Expert Review."""

from __future__ import annotations

from pathlib import Path

from app.integration.knowledge_reasoning import (
    build_expert_review_context,
    detect_expert_review_intent,
    expert_review_enabled,
    infer_document_kind,
    select_expert_role,
)


def test_expert_review_enabled_by_default() -> None:
    assert expert_review_enabled(Path(".")) is True


def test_detect_expert_review_intent_positive() -> None:
    assert detect_expert_review_intent("Профессиональный ли сам документ?")
    assert detect_expert_review_intent("What would you change in this business plan?")
    assert detect_expert_review_intent("Этот договор опасен для меня?")


def test_detect_expert_review_intent_negative_factual() -> None:
    assert not detect_expert_review_intent("Какой дедлайн указан в документе?")
    assert not detect_expert_review_intent("How many pages are in the PDF?")


def test_select_expert_role_from_question() -> None:
    assert select_expert_role("Опасен ли этот договор?", document_kind="generic") == "legal_reviewer"
    assert select_expert_role("Современный ли дизайн?", document_kind="generic") == "ux_expert"
    assert (
        select_expert_role("Что бы сказал инвестор?", document_kind="generic") == "investor"
    )


def test_select_expert_role_from_document_kind() -> None:
    assert (
        select_expert_role("Что думаешь?", document_kind="business_plan")
        == "business_consultant"
    )
    assert select_expert_role("Оцени", document_kind="resume") == "hr_reviewer"


def test_infer_document_kind() -> None:
    files = [{"filename": "plan.pdf", "parsed_excerpt": "Business plan for Virtus Core GmbH"}]
    assert infer_document_kind(files) == "business_plan"


def test_build_expert_review_context_document_not_author() -> None:
    files = [
        {
            "filename": "bizplan.pdf",
            "parsed_excerpt": "Geschäftsplan. Markt. Finanzen.",
        }
    ]
    ctx = build_expert_review_context(
        "Профессиональный ли этот документ?",
        files,
        memory_dir=Path("."),
        locale="ru",
    )
    assert "EXPERT REVIEW" in ctx
    assert "Бизнес-консультант" in ctx
    assert "не личность автора" in ctx.lower() or "не оценивай сертификаты" in ctx.lower()


def test_build_expert_review_skipped_without_parsed_text() -> None:
    files = [{"filename": "x.pdf", "parsed_excerpt": ""}]
    assert (
        build_expert_review_context("Профессиональный ли документ?", files, memory_dir=Path("."))
        == ""
    )
