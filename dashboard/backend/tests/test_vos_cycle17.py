"""VOS Validation — Cycle 17: scalability + Vector voice consistency."""

from __future__ import annotations

from pathlib import Path

import pytest

import app.execution.bridge as bridge
from app.execution.project_executors.registry import detect_project_intent, get_executor


@pytest.fixture
def memory_tmp(tmp_path: Path) -> Path:
    memory = tmp_path / "memory"
    memory.mkdir()
    return memory


def _first_turn(bridge_mod, msg: str, *, vid: str, memory: Path) -> dict:
    bridge_mod._REGISTRY = None
    out = bridge_mod.try_user_execution(msg, visitor_id=vid, memory_dir=memory)
    assert out is not None, msg
    return out


def _pm_voice(answer: str) -> str:
    """Normalize first line for comparison — Vector must sound the same."""
    return answer.split("\n", 1)[0].strip()


def test_inventory_executor_plugs_without_bridge_changes():
    """Cycle 17 — new executor file only; bridge/commerce/journey unchanged."""
    intent = detect_project_intent("Хочу автоматизировать учёт товаров на складе")
    assert intent is not None
    assert intent["service_id"] == "inventory"
    ex = get_executor("inventory")
    assert ex.service_id == "inventory"


def test_vos_five_scenarios_same_pm_first_line(memory_tmp: Path):
    scenarios = [
        ("vos-site", "Хочу создать сайт для своей компании."),
        ("vos-crm", "Хочу CRM для отдела продаж"),
        ("vos-auto", "Хочу автоматизировать склад"),
        ("vos-ai-sales", "Хочу AI-сотрудника для продаж"),
        ("vos-leads", "Хочу автоматизировать обработку заявок"),
    ]
    first_lines: list[str] = []
    for vid, msg in scenarios:
        out = _first_turn(bridge, msg, vid=vid, memory=memory_tmp)
        assert out["provider"] == "execution"
        assert "Проект создан" in out["answer"]
        assert "crm" not in out["answer"].lower() or "проект создан" in out["answer"].lower()
        assert "executor" not in out["answer"].lower()
        first_lines.append(_pm_voice(out["answer"]))
    assert len(set(first_lines)) == 1, first_lines


def test_vos_three_messages_hide_executor(memory_tmp: Path):
    """After 3 turns client cannot tell which executor runs."""
    vid = "vos-crm-hide"
    msgs = [
        "Хочу CRM для отдела продаж",
        "Компания NordWerk, отдел из 8 менеджеров.",
        "Нужно видеть лиды и этапы сделок без потерь.",
    ]
    bridge._REGISTRY = None
    for m in msgs:
        out = bridge.try_user_execution(m, visitor_id=vid, memory_dir=memory_tmp)
        assert out is not None
        assert "executor" not in out["answer"].lower()
        assert "llm" not in out["answer"].lower()
        assert "bridge" not in out["answer"].lower()


def test_inventory_routes_to_inventory_executor(memory_tmp: Path):
    out = _first_turn(
        bridge,
        "Хочу автоматизировать учёт товаров на складе",
        vid="vos-inventory",
        memory=memory_tmp,
    )
    assert "Проект создан" in out["answer"]
    assert (out.get("context") or {}).get("co_design") is True
