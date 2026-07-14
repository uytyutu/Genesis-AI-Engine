"""Cycle 16 — Project Bridge: three live paths, same PM voice."""

from __future__ import annotations

from pathlib import Path

import pytest

import app.execution.bridge as bridge


@pytest.fixture
def memory_tmp(tmp_path: Path) -> Path:
    memory = tmp_path / "memory"
    memory.mkdir()
    return memory


def _run(bridge_mod, msg: str, *, vid: str, memory: Path):
    return bridge_mod.try_user_execution(msg, visitor_id=vid, memory_dir=memory)


def test_three_projects_same_pm_voice_first_turn(memory_tmp: Path):
    bridge._REGISTRY = None
    scenarios = [
        (
            "cycle16-site",
            "Хочу создать сайт для своей компании.",
            "Проект создан",
            "website",
        ),
        (
            "cycle16-crm",
            "Хочу CRM для отдела продаж",
            "Проект создан",
            "crm",
        ),
        (
            "cycle16-auto",
            "Хочу автоматизировать склад",
            "Проект создан",
            "automation",
        ),
    ]
    answers: list[str] = []
    for vid, first_msg, needle, service in scenarios:
        out = _run(bridge, first_msg, vid=vid, memory=memory_tmp)
        assert out is not None, f"no response for {service}"
        assert out["provider"] == "execution"
        assert needle in out["answer"], out["answer"][:120]
        assert out.get("context", {}).get("co_design") is True
        answers.append(out["answer"].split("\n", 1)[0])
    assert all(a.startswith("Проект создан") for a in answers)


def test_crm_path_reaches_first_concept(memory_tmp: Path):
    bridge._REGISTRY = None
    vid = "cycle16-crm-full"
    msgs = [
        "Хочу CRM для отдела продаж компании NordWerk.",
        "Нужно видеть все лиды и этапы сделок, менеджеры не должны терять заявки.",
        "Хорошо, продолжаем.",
    ]
    last = None
    for i, m in enumerate(msgs):
        last = _run(bridge, m, vid=vid, memory=memory_tmp)
        if i < 2:
            assert last is not None
    assert last is not None
    assert "первая версия" in last["answer"].lower()
    assert last.get("context", {}).get("service_id") == "crm"


def test_automation_commerce_same_as_site(memory_tmp: Path):
    bridge._REGISTRY = None
    vid = "cycle16-auto-commerce"
    responses = []
    for m in [
        "Хочу автоматизировать склад компании LogiPro.",
        "Нужно автоматически обновлять остатки и уведомлять менеджера при минимуме.",
        "Хорошо, продолжаем.",
        "Да, всё устраивает.",
        "Хочу заказать.",
    ]:
        out = _run(bridge, m, vid=vid, memory=memory_tmp)
        if out is not None:
            responses.append(out)
    assert any("первая версия" in r["answer"].lower() for r in responses)
    assert responses[-1].get("cta_href", "").startswith("/order")
    assert "сайтом" not in responses[-1]["answer"].lower()


def test_greenline_site_still_co_design(memory_tmp: Path):
    bridge._REGISTRY = None
    vid = "cycle16-greenline"
    out = _run(
        bridge,
        "Хочу создать сайт для своей компании.",
        vid=vid,
        memory=memory_tmp,
    )
    assert out is not None
    assert "Проект создан" in out["answer"]
    assert (out.get("context") or {}).get("journey_step") == "company"
