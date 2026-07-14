"""T-003.1 — Guided Execution + Energy Budget (GMB evening slices)."""

from __future__ import annotations

from pathlib import Path

import app.execution.bridge as bridge
from app.integration.vector_intelligence.guided_execution import (
    try_guided_execution_route,
)


def _run(msg: str, *, vid: str, memory: Path, history: list[dict[str, str]] | None = None):
    bridge._REGISTRY = None
    return bridge.try_user_execution(
        msg,
        visitor_id=vid,
        memory_dir=memory,
        history=history,
    )


def _gmb_history() -> list[dict[str, str]]:
    return [
        {
            "role": "user",
            "content": "Строительная бригада BauTeam Köln в Кёльне, мало заказов.",
        },
        {
            "role": "assistant",
            "content": "Первые шаги: оформить Google Business Profile",
        },
    ]


def test_bauteam_evening_slice_one_action(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    vid = "t031-bauteam"
    msg1 = "У меня небольшая строительная фирма BauTeam Köln в Кёльне. Клиентов мало, всё в Excel."
    out1 = _run(msg1, vid=vid, memory=memory)
    assert out1 is not None
    assert "Google Business" in out1["answer"]

    history = [
        {"role": "user", "content": msg1},
        {"role": "assistant", "content": out1["answer"]},
    ]
    out2 = _run("Покажи как для тупого", vid=vid, memory=memory, history=history)
    assert out2 is not None
    assert out2.get("provider") == "execution"
    assert out2["context"]["guided_execution"] is True
    assert out2["context"].get("energy_budget") is True
    assert "одно действие" in out2["answer"].lower()
    assert "на сегодня" in out2["answer"].lower()
    assert "завтра" in out2["answer"].lower()
    assert "business.google.com" in out2["answer"] or any(
        "business.google.com" in a.get("href", "")
        for a in (out2.get("cta_actions") or [])
    )
    assert "[.]" not in out2["answer"]


def test_done_stops_for_today_not_next_step(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    vid = "t031-stop"
    history = _gmb_history()
    start = try_guided_execution_route(
        "Покажи по шагам",
        visitor_id=vid,
        memory_dir=memory,
        history=history,
    )
    assert start is not None
    assert start["context"]["step"] == 1

    stop = try_guided_execution_route(
        "Готово",
        visitor_id=vid,
        memory_dir=memory,
        history=history,
    )
    assert stop is not None
    assert stop["context"].get("evening_paused") is True
    assert "на сегодня достаточно" in stop["answer"].lower()
    assert "завтра" in stop["answer"].lower()
    assert stop["context"]["step"] == 2


def test_continue_next_evening(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    vid = "t031-continue"
    history = _gmb_history()
    try_guided_execution_route("Покажи как", visitor_id=vid, memory_dir=memory, history=history)
    try_guided_execution_route("Готово", visitor_id=vid, memory_dir=memory, history=history)

    nxt = try_guided_execution_route(
        "Продолжаем",
        visitor_id=vid,
        memory_dir=memory,
        history=history,
    )
    assert nxt is not None
    assert "вчера" in nxt["answer"].lower()
    assert nxt["context"]["step"] == 2


def test_guide_completes_across_evenings(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    vid = "t031-complete"
    history = _gmb_history()
    try_guided_execution_route(
        "Не умею, покажи как",
        visitor_id=vid,
        memory_dir=memory,
        history=history,
    )
    out = None
    for evening in range(5):
        out = try_guided_execution_route(
            "Готово",
            visitor_id=vid,
            memory_dir=memory,
            history=history,
        )
        if evening < 4:
            try_guided_execution_route(
                "Продолжаем",
                visitor_id=vid,
                memory_dir=memory,
                history=history,
            )
    assert out is not None
    assert out["context"]["completed"] is True


def test_no_guide_without_gmb_context(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    out = try_guided_execution_route(
        "Покажи как сделать CRM",
        visitor_id="t031-no",
        memory_dir=memory,
        history=[],
    )
    assert out is None
