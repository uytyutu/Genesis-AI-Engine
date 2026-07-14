"""VOS Validation — Cycle 18: company as main object, expansion not repurchase."""

from __future__ import annotations

from pathlib import Path

import pytest

import app.execution.bridge as bridge
from app.execution.project_bridge.company_memory import load_company_memory
from app.integration.product_line import SERVICE_CRM, SERVICE_SEO, SERVICE_WEBSITE


@pytest.fixture
def memory_tmp(tmp_path: Path) -> Path:
    memory = tmp_path / "memory"
    memory.mkdir()
    return memory


def _run(bridge_mod, msg: str, *, vid: str, memory: Path):
    bridge_mod._REGISTRY = None
    return bridge_mod.try_user_execution(msg, visitor_id=vid, memory_dir=memory)


def _establish_site_company(memory: Path, vid: str = "cycle18-greenline") -> None:
    """Day 1 — site + company identity."""
    for msg in [
        "Хочу создать сайт для компании GreenLine.",
        "GreenLine — тёплый минимализм, аудитория B2B в Германии.",
        "Хорошо, продолжаем.",
    ]:
        out = _run(bridge, msg, vid=vid, memory=memory)
        assert out is not None, msg


def test_company_memory_persists_after_site(memory_tmp: Path):
    _establish_site_company(memory_tmp)
    mem = load_company_memory(memory_tmp, "cycle18-greenline")
    assert mem is not None
    assert mem.company_name == "GreenLine"
    assert SERVICE_WEBSITE in mem.services


def test_crm_expansion_continues_company_not_new_purchase(memory_tmp: Path):
    """Day 12 — CRM on existing company."""
    vid = "cycle18-crm-expand"
    _establish_site_company(memory_tmp, vid=vid)
    out = _run(bridge, "Через неделю хочу CRM для отдела продаж", vid=vid, memory=memory_tmp)
    assert out is not None
    answer = out["answer"].lower()
    assert "greenline" in answer
    assert "цифров" in answer or "существующ" in answer or "добавим" in answer
    assert "как называется" not in answer
    assert "название компании" not in answer
    ctx = out.get("context") or {}
    assert ctx.get("expansion_mode") is True
    assert ctx.get("service_id") == SERVICE_CRM


def test_ai_employee_links_to_prior_services(memory_tmp: Path):
    """Day 18 — AI employee uses prior context."""
    vid = "cycle18-ai-expand"
    _establish_site_company(memory_tmp, vid=vid)
    _run(bridge, "Хочу CRM для отдела продаж", vid=vid, memory=memory_tmp)
    out = _run(
        bridge,
        "Теперь нужен AI-сотрудник для продаж",
        vid=vid,
        memory=memory_tmp,
    )
    assert out is not None
    answer = out["answer"].lower()
    assert "ai" in answer or "сотрудник" in answer
    assert "greenline" in answer
    assert "с нуля" not in answer or "не начинаем" in answer


def test_seo_optimizes_existing_site(memory_tmp: Path):
    """Day 27 — SEO on existing website."""
    vid = "cycle18-seo-expand"
    _establish_site_company(memory_tmp, vid=vid)
    out = _run(
        bridge,
        "Теперь нужно SEO для продвижения сайта",
        vid=vid,
        memory=memory_tmp,
    )
    assert out is not None
    answer = out["answer"].lower()
    assert "оптимиз" in answer or "seo" in answer
    assert "greenline" in answer
    assert "существующ" in answer or "уже" in answer


def test_forty_day_journey_feels_one_company(memory_tmp: Path):
    """Blind owner — site → CRM → AI → SEO → automation."""
    vid = "cycle18-journey"
    _establish_site_company(memory_tmp, vid=vid)
    _run(bridge, "Измени блок с отзывами — сделай компактнее", vid=vid, memory=memory_tmp)

    expansion_turns = [
        ("Хочу CRM для учёта клиентов", ("crm", "добавим", "greenline")),
        ("Нужен AI-сотрудник для обработки заявок", ("ai", "greenline")),
        ("Нужно SEO для продвижения сайта", ("seo", "оптимиз", "greenline")),
        ("Добавь автоматизацию заявок", ("автоматиз", "greenline")),
    ]
    company_questions = 0
    for msg, needles in expansion_turns:
        out = _run(bridge, msg, vid=vid, memory=memory_tmp)
        assert out is not None, msg
        low = out["answer"].lower()
        if "как называется" in low or "название компании" in low:
            company_questions += 1
        for n in needles:
            assert n in low, f"missing {n!r} in {out['answer'][:200]}"

    assert company_questions == 0, "Vector re-asked company name during expansion"

    mem = load_company_memory(memory_tmp, vid)
    assert mem is not None
    assert mem.company_name == "GreenLine"
    assert len(mem.services) >= 2


def test_resolve_prefers_new_service_on_expansion(memory_tmp: Path):
    from app.execution.project_executors.registry import resolve_service_id

    vid = "cycle18-resolve"
    _establish_site_company(memory_tmp, vid=vid)
    svc = resolve_service_id(
        "Хочу CRM для отдела продаж",
        memory_dir=memory_tmp,
        visitor_id=vid,
    )
    assert svc == SERVICE_CRM


def test_seo_service_id_on_expansion(memory_tmp: Path):
    from app.execution.project_executors.registry import resolve_service_id

    vid = "cycle18-seo-resolve"
    _establish_site_company(memory_tmp, vid=vid)
    svc = resolve_service_id(
        "Нужно SEO для продвижения",
        memory_dir=memory_tmp,
        visitor_id=vid,
    )
    assert svc == SERVICE_SEO
