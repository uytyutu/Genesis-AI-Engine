"""50 Genesis dialogues — Human Intelligence v1 dogfooding proof."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))

from app.integration.genesis_ai_knowledge import build_system_prompt
from app.integration.genesis_brain import GenesisBrain
from app.integration.genesis_brain.layers.memory import GenesisMemoryLayer

# (title, visitor_id, message, history, mode)
SCENARIOS: list[tuple] = [
    ("Привет 1", "d01", "Привет", []),
    ("Привет 2", "d02", "Привет", []),
    ("Как дела", "d03", "Как дела?", []),
    ("Грустно", "d04", "Мне грустно", []),
    ("Квантовая физика", "d05", "Объясни квантовую физику простыми словами", []),
    ("Шутка", "d06", "Расскажи шутку", []),
    ("Опечатка: хачу сайт", "d07", "хачу сайт", []),
    ("Опечатка: придкмай бизнес", "d08", "придкмай мне бизнес проект", []),
    ("Опечатка: аткрой кофейню", "d09", "аткрой кофейню", []),
    ("Опечатка: хачу чатбот", "d10", "хачу чатбот", []),
    ("Бизнес старт", "d11", "Хочу открыть бизнес", []),
    ("Идея в контексте", "d12", "придумай идею", [
        {"role": "user", "content": "Хочу открыть бизнес"},
        {"role": "assistant", "content": "Отлично — давайте подберём направление."},
    ]),
    ("Бюджет", "d13", "Бюджет 20000€", [
        {"role": "user", "content": "Хочу открыть бизнес"},
        {"role": "assistant", "content": "В какой стране?"},
    ]),
    ("Германия", "d14", "Я из Германии", []),
    ("Кофейня", "d15", "Хочу открыть кофейню", []),
    ("Сайт", "d16", "Нужен сайт", [
        {"role": "user", "content": "Хочу кофейню"},
        {"role": "assistant", "content": "Отлично."},
    ]),
    ("Приложение", "d17", "Нужно приложение", []),
    ("Продвижение", "d18", "Нужно продвижение", []),
    ("Studio", "d19", "Хочу пользоваться Studio", []),
    ("Письмо", "d20", "Помоги написать деловое письмо", []),
    ("Салон", "d21", "Сайт для салона красоты", []),
    ("Магазин", "d22", "Интернет-магазин одежды", []),
    ("Автосервис", "d23", "Сайт автосервиса", []),
    ("Telegram", "d24", "Telegram бот для записи", []),
    ("Factory", "d25", "Что такое Factory?", []),
    ("Marketing Lab", "d26", "Расскажи про Marketing Lab", []),
    ("Кто ты", "d27", "Кто ты?", []),
    ("Повышение", "d28", "Я получил повышение!", []),
    ("Устал", "d29", "Очень устал сегодня", []),
    ("Спасибо", "d30", "Спасибо, помогли", []),
    ("English", "d31", "Hello", []),
    ("Космос", "d32", "Расскажи про чёрные дыры", []),
    ("Не знаю", "d33", "Не знаю какой бизнес", [
        {"role": "user", "content": "Хочу бизнес"},
        {"role": "assistant", "content": "Ок."},
    ]),
    ("Имя память", "d34", "Как меня зовут?", [
        {"role": "user", "content": "Меня зовут Алекс."},
        {"role": "assistant", "content": "Приятно познакомиться."},
    ]),
    ("Возврат", "d35", "Привет снова", []),
    ("Длинный контекст", "d36", "А сайт?", [
        {"role": "user", "content": "Хочу кофейню в Берлине"},
        {"role": "assistant", "content": "Хорошая ниша."},
        {"role": "user", "content": "Бюджет 15000"},
        {"role": "assistant", "content": "Реалистично."},
    ]),
    ("AI на сайте", "d37", "Хочу AI консультанта на сайте", []),
    ("Подписка выгода", "d38", "Чем Studio лучше одного сайта?", []),
    ("Возражение дорого", "d39", "350 евро дорого для сайта", []),
    ("Два проекта", "d40", "Планирую 3 сайта в год", []),
    ("Прощание", "d41", "Пока, до завтра", []),
    ("Наука 2", "d42", "Что такое суперпозиция?", []),
    ("Эмоция 2", "d43", "Мне страшно начинать", []),
    ("Бизнес идея 2", "d44", "Идея для онлайн школы", []),
    ("Бот опечатка", "d45", "нужен телеграмм бот", []),
    ("Кафе опечатка", "d46", "сайт для кафе", []),
    ("Общий", "d47", "Помоги разобраться", []),
    ("CEO утро", "ceo1", "Доброе утро", [], "ceo"),
    ("Повтор привет", "d48", "Привет", []),
    ("Повтор привет 2", "d49", "Привет", []),
    ("Повтор привет 3", "d50", "Привет", []),
]

BANNED = ("расскажите о задаче", "я вас не понял", "notallowederror", "permission denied")


def main() -> None:
    out = ROOT / "scripts" / "_genesis_50_dialogues.txt"
    tmp = Path(tempfile.mkdtemp())
    mem = GenesisMemoryLayer(tmp)
    mem.save("d35", {"visitor_id": "d35", "visit_count": 3, "facts": [], "milestones": []})

    brain = GenesisBrain(memory_dir=tmp, packages=[])
    system = build_system_prompt([])

    lines = ["=" * 60, "GENESIS — 50 ДИАЛОГОВ (Human Intelligence v1)", "=" * 60]
    violations: list[str] = []
    answers: list[str] = []

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
        ans = result.answer
        answers.append(ans)
        low = ans.lower()
        for b in BANNED:
            if b in low:
                violations.append(f"{title}: banned '{b}'")

        lines.append(f"\n### {title}")
        lines.append(f"Пользователь: {question}")
        lines.append(f"Genesis:\n{ans}")
        lines.append("-" * 40)

    # Variation check: 3 identical greetings should not be identical
    greet_answers = [a for (t, _, q, *_), a in zip(SCENARIOS, answers) if q == "Привет" and t.startswith("Привет")]
    if len(greet_answers) >= 3 and len(set(greet_answers)) < 2:
        violations.append("Greeting variation: 3+ привет gave identical answers")

    lines.append(f"\n\nVIOLATIONS: {len(violations)}")
    for v in violations:
        lines.append(f"  - {v}")

    text = "\n".join(lines)
    out.write_text(text, encoding="utf-8")
    print(text[-2000:])
    print(f"\nWrote {out}")
    if violations:
        sys.exit(1)


if __name__ == "__main__":
    main()
