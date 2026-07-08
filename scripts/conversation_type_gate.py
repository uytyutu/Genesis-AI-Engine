#!/usr/bin/env python3
"""Anti-sales gate — personal talks must never become website/Factory pitches."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))

from app.integration.genesis_brain import GenesisBrain  # noqa: E402

_SALES_MARKERS = (
    "6 страниц",
    "650–850",
    "650–950",
    "studio basic",
    "49 €/мес",
    "genesis factory",
    "factory —",
    "запись клиентов через сайт",
    "ориентир под ключ",
)

_PERSONAL_PROMPTS = [
    "Как думаешь, я стану успешным?",
    "Я хочу стать миллионером",
    "Смогу ли я добиться успеха?",
    "Как ты думаешь, у меня получится?",
    "Мне плохо сегодня",
    "Что такое чёрная дыра?",
    "Привет, как дела?",
    "Давай просто поговорим",
    "Я боюсь, что у меня ничего не выйдет",
    "В чём смысл жизни?",
    "Помоги написать игру на Python",
    "Расскажи анекдот",
    "Я устал от работы",
    "Думаешь, я смогу разбогатеть?",
    "Как думаешь, стоит ли мне менять профессию?",
    "Мне одиноко",
    "Что ты думаешь о будущем?",
    "Я хочу быть счастливым",
    "Получится ли у меня?",
    "Как ты считаешь, я на правильном пути?",
]


def main() -> int:
    tmp = ROOT / "memory" / "conversation_type_gate_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    brain = GenesisBrain(memory_dir=tmp, packages=[])
    violations: list[dict] = []

    for i, prompt in enumerate(_PERSONAL_PROMPTS):
        vid = f"gate-{i}"
        r = brain.chat(
            system="",
            messages=[{"role": "user", "content": prompt}],
            visitor_id=vid,
        )
        low = r.answer.lower()
        hits = [m for m in _SALES_MARKERS if m.lower() in low]
        if hits:
            violations.append({"prompt": prompt, "markers": hits, "answer": r.answer[:200]})

    out = {
        "prompts": len(_PERSONAL_PROMPTS),
        "violations": len(violations),
        "pass": not violations,
        "details": violations,
    }
    path = ROOT / "scripts" / "conversation_type_gate_results.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Conversation type gate: {len(_PERSONAL_PROMPTS) - len(violations)}/{len(_PERSONAL_PROMPTS)} PASS")
    for v in violations:
        print(f"  FAIL {v['prompt']!r} -> {v['markers']}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
