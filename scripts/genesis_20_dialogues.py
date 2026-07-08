"""20 live Genesis dialogues — personality calibration proof."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))

from app.integration.genesis_ai_knowledge import build_system_prompt
from app.integration.genesis_brain import GenesisBrain
from app.integration.genesis_brain.layers.memory import GenesisMemoryLayer

SCENARIOS = [
    ("1. Первая встреча", "dialogue-1", "Привет", []),
    ("2. Вторая встреча (другой визит)", "dialogue-2", "Привет", []),
    ("3. Возвращение с именем", "dialogue-3", "Привет", []),
    ("4. Повышение", "dialogue-4", "Я сегодня получил повышение на работе.", []),
    ("5. Тяжело", "dialogue-5", "Мне тяжело.", []),
    ("6. Усталость", "dialogue-6", "Я сегодня очень устал.", []),
    ("7. Земля плоская", "dialogue-7", "Земля плоская.", []),
    ("8. Сайт для кафе", "dialogue-8", "Хочу сайт для кофейни.", []),
    ("9. Не знаю", "dialogue-9", "Не знаю, как лучше сделать.", []),
    ("10. Factory", "dialogue-10", "Что такое Factory?", []),
    ("11. Studio", "dialogue-11", "Расскажи про Genesis Studio.", []),
    ("12. Память — имя", "dialogue-12", "Как меня зовут?", [
        {"role": "user", "content": "Меня зовут Рамиш."},
        {"role": "assistant", "content": "Приятно познакомиться."},
    ]),
    ("13. Хороший сон", "dialogue-13", "Я сегодня хорошо поспал.", []),
    ("14. Telegram-бот", "dialogue-14", "Нужен Telegram-бот для записи клиентов.", []),
    ("15. Marketing Lab", "dialogue-15", "Что такое Marketing Lab?", []),
    ("16. Благодарность", "dialogue-16", "Спасибо, вы очень помогли.", []),
    ("17. Идея бизнеса", "dialogue-17", "Помоги придумать бизнес в маленьком городе.", []),
    ("18. English", "dialogue-18", "Hello", []),
    ("19. Кто ты", "dialogue-19", "Кто ты такой?", []),
    ("20. CEO — утро", "ceo-1", "Доброе утро.", [], "ceo"),
]


def main() -> None:
    out_path = ROOT / "scripts" / "_genesis_20_dialogues.txt"
    tmp = Path(tempfile.mkdtemp())
    mem = GenesisMemoryLayer(tmp)

    # Seed returning user for scenario 3
    mem.save("dialogue-3", {"visitor_id": "dialogue-3", "name": "Анна", "visit_count": 4, "facts": [], "milestones": []})
    mem.save("dialogue-2", {"visitor_id": "dialogue-2", "name": None, "visit_count": 2, "facts": [], "milestones": []})

    brain = GenesisBrain(memory_dir=tmp, packages=[])
    system = build_system_prompt([])

    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("GENESIS — 20 ДИАЛОГОВ (Personality v1)")
    lines.append("=" * 60)

    for item in SCENARIOS:
        if len(item) == 5:
            title, vid, question, history, mode = item
        else:
            title, vid, question, history = item
            mode = "public"

        messages = brain.assemble_messages(history, question)
        result = brain.chat(
            system=system,
            messages=messages,
            visitor_id=vid,
            personality_mode=mode,  # type: ignore[arg-type]
        )
        lines.append(f"\n### {title}")
        lines.append(f"Пользователь: {question}")
        lines.append(f"Genesis:\n{result.answer}")
        lines.append("-" * 40)

    text = "\n".join(lines)
    out_path.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
