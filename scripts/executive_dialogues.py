#!/usr/bin/env python3
"""Executive Brain pivot scenarios — multi-turn dialogue proof (no markdown reports)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))

from app.integration.genesis_brain import GenesisBrain  # noqa: E402

_BANNED = (
    "расскажите о задаче",
    "я — genesis",
    "чем могу помочь",
    "что для вас важнее всего",
)

SCENARIOS: list[dict] = [
    {
        "id": "propose_first",
        "turns": ["Хочу открыть бизнес"],
        "must_contain": ["**1.", "предложил"],
        "must_not": ["в какой стране"],
    },
    {
        "id": "thanks_close",
        "turns": [
            "Хочу открыть бизнес",
            "Спасибо",
        ],
        "must_contain": ["продолжим"],
        "must_not": ["чем могу помочь", "что ещё"],
    },
    {
        "id": "pivot_germany_austria_ai",
        "turns": [
            "Я живу в Германии",
            "Переехал в Австрию",
            "50000 €",
            "Не кофейня",
            "Лучше онлайн",
            "Хочу AI компанию",
        ],
        "must_contain": [],
        "must_not": _BANNED,
        "final_state": {"country": "Австрия", "goal": "ai_company"},
    },
    {
        "id": "reject_no",
        "turns": [
            "Хочу открыть бизнес",
            "Нет",
        ],
        "must_contain": ["направлен"],
        "must_not": _BANNED,
    },
    {
        "id": "why_question",
        "turns": [
            "страна россия город москва бюджет минимальный",
            "10к рублей",
            "Почему?",
        ],
        "must_contain": [],
        "must_not": _BANNED,
    },
    {
        "id": "you_wrong",
        "turns": [
            "Хочу кофейню в Берлине",
            "Ты ошибся",
        ],
        "must_contain": ["поправ"],
        "must_not": _BANNED,
    },
    {
        "id": "life_goal_family",
        "turns": [
            "Хочу больше времени проводить с семьёй",
            "Хочу открыть бизнес",
        ],
        "must_contain": ["семь", "lean"],
        "must_not": _BANNED,
    },
]


def run_scenario(brain: GenesisBrain, scenario: dict, tmp: Path) -> dict:
    vid = f"exec-{scenario['id']}"
    msgs: list[dict[str, str]] = []
    violations: list[str] = []
    last_answer = ""

    for turn in scenario["turns"]:
        msgs.append({"role": "user", "content": turn})
        r = brain.chat(system="", messages=msgs, visitor_id=vid)
        last_answer = r.answer
        low = r.answer.lower()
        for b in _BANNED:
            if b in low:
                violations.append(f"banned:{b} in {turn!r}")
        msgs.append({"role": "assistant", "content": r.answer})

    low = last_answer.lower()
    for token in scenario.get("must_contain", []):
        if token.lower() not in low:
            violations.append(f"missing:{token}")
    for token in scenario.get("must_not", []):
        if token.lower() in low:
            violations.append(f"forbidden:{token}")

    state_check = scenario.get("final_state")
    state_ok = True
    if state_check:
        from app.integration.genesis_brain.layers.conversation_state import ConversationStateLayer
        from app.integration.genesis_brain.layers.memory import GenesisMemoryLayer

        st = ConversationStateLayer(GenesisMemoryLayer(tmp)).process(vid, msgs)
        for k, v in state_check.items():
            if getattr(st, k) != v:
                violations.append(f"state:{k}={getattr(st, k)!r} want {v!r}")
                state_ok = False

    return {
        "id": scenario["id"],
        "pass": not violations,
        "violations": violations,
        "last_answer_preview": last_answer[:200],
    }


def main() -> int:
    tmp = ROOT / "memory" / "executive_dialogues_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    brain = GenesisBrain(memory_dir=tmp, packages=[])
    results = [run_scenario(brain, s, tmp) for s in SCENARIOS]
    failed = [r for r in results if not r["pass"]]
    out = {"scenarios": len(results), "failed": len(failed), "results": results}
    out_path = ROOT / "scripts" / "executive_dialogues_results.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Executive dialogues: {len(results) - len(failed)}/{len(results)} PASS")
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  [{status}] {r['id']}")
        for v in r["violations"]:
            print(f"       - {v}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
