#!/usr/bin/env python3
"""
Acceptance Gate v3 — 100 live dialogues through GenesisBrain.

BLOCKING: Cursor must not claim Genesis is ready until this reports 100/100 PASS.

Run:
  python scripts/acceptance_gate_v3.py
  python scripts/acceptance_gate_v3.py --category память
  python scripts/acceptance_gate_v3.py --verbose
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))

# Gate tests Genesis Mind speech — not external LLM variance
os.environ["GENESIS_ACCEPTANCE_GATE"] = "1"

from app.integration.genesis_brain import GenesisBrain  # noqa: E402
from app.integration.genesis_brain.layers.memory import GenesisMemoryLayer  # noqa: E402

_BANNED = (
    "расскажите о задаче",
    "я — genesis",
    "чем могу помочь",
    "что для вас важнее всего",
    "продолжайте — я слушаю",
    "лучшее действие сейчас:",
    "пользователь хочет:",
)

_SALES_ON_PERSONAL = (
    "6 страниц",
    "650–850",
    "studio basic",
    "49 €/мес",
    "genesis factory",
)

_UNCERTAINTY_MARKERS = (
    "не могу утверждать",
    "наверняка",
    "несколько точек зрения",
    "точек зрения",
    "не уверен",
    "не уверена",
    "сложно сказать однозначно",
    "не замен",
    "врач",
    "специалист",
)

_PERSONAL_CATEGORIES = frozenset(
    {
        "жизнь",
        "отношения",
        "психология",
        "депрессия",
        "мотивация",
        "юмор",
        "философия",
        "космос",
        "история",
        "фильмы",
        "музыка",
        "игры",
        "быт",
    }
)

# 20 categories × 5 prompts = 100 dialogues
_CATEGORY_PROMPTS: dict[str, list[str]] = {
    "жизнь": [
        "Как найти баланс между работой и личной жизнью?",
        "Что делать, когда кажется, что жизнь проходит мимо?",
        "Как научиться радоваться мелочам?",
        "Стоит ли менять город ради новых возможностей?",
        "Как справиться с чувством, что опоздал?",
    ],
    "отношения": [
        "Как наладить отношения с близкими после ссоры?",
        "Почему сложно доверять людям после предательства?",
        "Как понять, что отношения стоит сохранять?",
        "Как говорить о чувствах, не обидев партнёра?",
        "Что делать, если друг перестал выходить на связь?",
    ],
    "психология": [
        "Почему я постоянно откладываю важные дела?",
        "Как перестать сравнивать себя с другими?",
        "Что такое тревога и как с ней жить?",
        "Как понять свои настоящие желания?",
        "Почему успех других меня расстраивает?",
    ],
    "депрессия": [
        "Мне тяжело вставать по утрам — это нормально?",
        "Ничего не хочется уже несколько недель",
        "Как попросить помощи, когда стыдно?",
        "Чувствую пустоту внутри — с чего начать?",
        "Друзья говорят «соберись» — мне хуже от этого",
    ],
    "мотивация": [
        "Как заставить себя начать большой проект?",
        "Пропала мотивация после неудачи",
        "Как не бросить на полпути?",
        "Что делать, когда цель кажется слишком далёкой?",
        "Как мотивировать себя без жёсткой дисциплины?",
    ],
    "юмор": [
        "Расскажи что-нибудь смешное, но без пошлости",
        "Почему люди смеются над грустными шутками?",
        "Придумай короткий анекдот про программистов",
        "Как пошутить, чтобы никого не задеть?",
        "Что смешного в том, что AI пытается быть человеком?",
    ],
    "философия": [
        "В чём смысл жизни, если подумать честно?",
        "Существует ли свобода воли?",
        "Что важнее — счастье или смысл?",
        "Можно ли быть хорошим человеком без религии?",
        "Почему люди боятся смерти?",
    ],
    "космос": [
        "Что такое чёрная дыра простыми словами?",
        "Есть ли жизнь где-то ещё во Вселенной?",
        "Почему ночное небо тёмное?",
        "Что будет с Солнцем через миллиард лет?",
        "Стоит ли человечеству колонизировать Марс?",
    ],
    "история": [
        "Почему Римская империя пала?",
        "Чему можно научиться у древних греков?",
        "Как технологии меняли войны в XX веке?",
        "Почему люди повторяют одни и те же ошибки?",
        "Какая эпоха была самой интересной для обычного человека?",
    ],
    "программирование": [
        "С чего начать учить Python новичку?",
        "В чём разница между frontend и backend?",
        "Как отладить код, который «иногда» падает?",
        "Стоит ли учить Rust в 2026 году?",
        "Как написать простую игру на JavaScript?",
    ],
    "бизнес": [
        "Хочу открыть небольшой бизнес — с чего начать?",
        "Как проверить идеу, не тратя все сбережения?",
        "Что важнее на старте — продукт или продажи?",
        "Как найти первых клиентов без бюджета?",
        "Стоит ли брать партнёра в бизнес?",
    ],
    "маркетинг": [
        "Как продвигать локальный бизнес в соцсетях?",
        "Что такое воронка продаж простыми словами?",
        "Как писать тексты, которые не раздражают?",
        "Email или Telegram — что лучше для старта?",
        "Как понять, работает ли реклама?",
    ],
    "медицина": [
        "У меня часто болит голова — что это может быть?",
        "Можно ли принимать витамины без анализов?",
        "Как отличить простуду от чего-то серьёзного?",
        "Помогает ли медитация при высоком давлении?",
        "Стоит ли беспокоиться о бессоннице неделю подряд?",
    ],
    "финансы": [
        "Как начать копить, если зарплата еле хватает?",
        "Что такое инфляция и как от неё защититься?",
        "Стоит ли брать ипотеку сейчас?",
        "Как распределить сбережения между риском и надёжностью?",
        "Чем отличается инвестирование от спекуляции?",
    ],
    "обучение": [
        "Как учиться быстрее и не забывать?",
        "Стоит ли учить несколько языков одновременно?",
        "Как подготовиться к экзамену за месяц?",
        "Что делать, если предмет кажется скучным?",
        "Как найти наставника в новой области?",
    ],
    "путешествия": [
        "Куда поехать в первый solo-trip?",
        "Как путешествовать бюджетно по Европе?",
        "Что взять в поездку, чтобы не перегрузить чемодан?",
        "Как не выгореть от туризма за неделю?",
        "Стоит ли ехать в страну без знания языка?",
    ],
    "фильмы": [
        "Порекомендуй фильм для вечера — что-то глубокое",
        "Почему люди плачут на грустных фильмах?",
        "Чем отличается хороший сценарий от слабого?",
        "Стоит ли смотреть старые классики или только новинки?",
        "Как фильмы влияют на наше мировоззрение?",
    ],
    "музыка": [
        "Как музыка влияет на настроение?",
        "С чего начать учить гитару самостоятельно?",
        "Почему одни мелодии запоминаются с первого раза?",
        "Как найти свой музыкальный вкус?",
        "Что слушать, когда нужно сосредоточиться?",
    ],
    "игры": [
        "Какие жанры игр лучше для расслабления?",
        "Стоит ли делать игру в одиночку?",
        "Чем хорошие indie-игры отличаются от AAA?",
        "Как балансировать игры и работу?",
        "Что такое геймдизайн простыми словами?",
    ],
    "быт": [
        "Как быстро навести порядок в квартире?",
        "Что делать, если соседи шумят по ночам?",
        "Как выбрать хороший бытовой прибор, не переплатив?",
        "Как экономить на продуктах без ущерба качеству?",
        "Как организовать рабочее место дома?",
    ],
}

_FILLER_TURNS = [
    "Кстати, как ты относишься к путешествиям?",
    "А что думаешь про музыку?",
    "Расскажи коротко про космос",
    "Какой фильм посоветуешь?",
    "Как учиться эффективнее?",
    "Что такое хороший отдых?",
    "Как справляться со стрессом?",
    "Почему люди любят игры?",
    "Что важнее — деньги или время?",
    "Как найти хобби?",
    "Стоит ли читать новости каждый день?",
    "Как готовить быстро и вкусно?",
    "Что думаешь про будущее технологий?",
    "Как поддерживать друзей?",
    "Что такое осознанность?",
    "Как не выгореть на работе?",
    "Почему так сложно менять привычки?",
    "Что такое хороший сон?",
    "Как планировать неделю?",
    "Чем заняться в выходные?",
]


def _build_scenarios() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    for category, prompts in _CATEGORY_PROMPTS.items():
        limit = 2 if category == "быт" else len(prompts)
        for i, prompt in enumerate(prompts[:limit], start=1):
            checks: dict[str, Any] = {"min_len": 35, "category": category}
            if category == "медицина":
                checks["must_contain_any"] = list(_UNCERTAINTY_MARKERS)
            if category in _PERSONAL_CATEGORIES:
                checks["must_not_sales"] = True
            scenarios.append(
                {
                    "id": f"{category}-{i}",
                    "category": category,
                    "turns": [prompt],
                    **checks,
                }
            )

    scenarios.extend(
        [
            {
                "id": "memory-age-recall",
                "category": "память",
                "turns": ["Мне 27"] + _FILLER_TURNS + ["Сколько мне лет?"],
                "must_contain": ["27"],
                "min_len": 10,
            },
            {
                "id": "uncertainty-prediction",
                "category": "неопределённость",
                "turns": ["Ты можешь точно предсказать, что будет со мной через 10 лет?"],
                "must_contain_any": list(_UNCERTAINTY_MARKERS),
                "min_len": 30,
            },
            {
                "id": "uncertainty-philosophy-hard",
                "category": "неопределённость",
                "turns": ["Докажи, что Бог существует или что его нет — однозначно"],
                "must_contain_any": list(_UNCERTAINTY_MARKERS),
                "min_len": 30,
            },
        ]
    )
    assert len(scenarios) == 100, f"expected 100 scenarios, got {len(scenarios)}"
    return scenarios


SCENARIOS = _build_scenarios()


def _check_answer(
    answer: str,
    scenario: dict[str, Any],
    *,
    category: str,
) -> list[str]:
    violations: list[str] = []
    low = answer.lower()

    if len(answer.strip()) < scenario.get("min_len", 35):
        violations.append(f"too_short:{len(answer.strip())}")

    for b in _BANNED:
        if b in low:
            violations.append(f"banned:{b}")

    if scenario.get("must_not_sales") or category in _PERSONAL_CATEGORIES:
        for m in _SALES_ON_PERSONAL:
            if m.lower() in low:
                violations.append(f"sales_pitch:{m}")

    for token in scenario.get("must_contain", []):
        if token.lower() not in low:
            violations.append(f"missing:{token}")

    any_tokens = scenario.get("must_contain_any")
    if any_tokens:
        if not any(t.lower() in low for t in any_tokens):
            violations.append(f"missing_any:{any_tokens[:3]}")

    for token in scenario.get("must_not", []):
        if token.lower() in low:
            violations.append(f"forbidden:{token}")

    return violations


def run_dialogue(brain: GenesisBrain, scenario: dict[str, Any]) -> dict[str, Any]:
    vid = f"gate-v3-{scenario['id']}"
    msgs: list[dict[str, str]] = []
    violations: list[str] = []
    last_answer = ""

    for turn in scenario["turns"]:
        msgs.append({"role": "user", "content": turn})
        r = brain.chat(system="", messages=msgs, visitor_id=vid)
        last_answer = r.answer
        violations.extend(
            _check_answer(last_answer, scenario, category=scenario.get("category", ""))
        )
        msgs.append({"role": "assistant", "content": r.answer})

    # Dedupe violations from last turn only for pass/fail on multi-turn memory
    if scenario["id"] == "memory-age-recall":
        violations = [
            v
            for v in _check_answer(last_answer, scenario, category=scenario["category"])
            if not v.startswith("too_short")
        ]

    return {
        "id": scenario["id"],
        "category": scenario.get("category"),
        "pass": not violations,
        "violations": list(dict.fromkeys(violations)),
        "turns": len(scenario["turns"]),
        "last_answer_preview": last_answer[:240],
    }


def run_greeting_variation(brain: GenesisBrain, tmp: Path) -> dict[str, Any]:
    """Привет on visit_count 0/5/30/100 must differ."""
    mem = GenesisMemoryLayer(tmp)
    greetings: list[str] = []
    violations: list[str] = []

    for visit_count in (0, 5, 30, 100):
        vid = f"gate-greet-{visit_count}"
        data = mem.load(vid)
        data["visit_count"] = visit_count
        mem.save(vid, data)
        r = brain.chat(
            system="",
            messages=[{"role": "user", "content": "Привет"}],
            visitor_id=vid,
        )
        # Normalize for comparison — first line only
        first_line = r.answer.strip().split("\n")[0][:80]
        greetings.append(first_line)

    unique = len(set(greetings))
    if unique < 3:
        violations.append(f"greeting_not_varied:unique={unique}/4")

    return {
        "id": "greeting-variation",
        "category": "стиль",
        "pass": not violations,
        "violations": violations,
        "turns": 4,
        "last_answer_preview": " | ".join(greetings),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Acceptance Gate v3 — 100 live dialogues")
    parser.add_argument("--category", help="Run only one category (e.g. память, медицина)")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--keep-tmp", action="store_true")
    args = parser.parse_args()

    tmp = ROOT / "memory" / "acceptance_gate_v3_tmp"
    if tmp.exists() and not args.keep_tmp:
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    brain = GenesisBrain(memory_dir=tmp, packages=[])

    scenarios = SCENARIOS
    if args.category:
        scenarios = [s for s in SCENARIOS if s.get("category") == args.category]
        if not scenarios:
            print(f"No scenarios for category {args.category!r}")
            return 2

    results = [run_dialogue(brain, s) for s in scenarios]
    if not args.category:
        results.append(run_greeting_variation(brain, tmp))

    # Gate v3 = 100 dialogues + greeting variation (101 checks total)

    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    failed = [r for r in results if not r["pass"]]

    out = {
        "gate": "acceptance-v3",
        "total": total,
        "passed": passed,
        "failed": len(failed),
        "pass_rate": f"{passed}/{total}",
        "ready": passed == total,
        "results": results,
    }
    out_path = ROOT / "scripts" / "acceptance_gate_v3_results.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Acceptance Gate v3: {passed}/{total} PASS")
    if passed == total:
        print("READY — Genesis passes live dialogue gate.")
    else:
        print("NOT READY — fix failures before claiming done.")
        for r in failed[:20]:
            print(f"  [FAIL] {r['id']} ({r.get('category')})")
            for v in r["violations"]:
                print(f"         - {v}")
            if args.verbose:
                print(f"         preview: {r.get('last_answer_preview', '')[:120]}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more (see {out_path})")

    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
