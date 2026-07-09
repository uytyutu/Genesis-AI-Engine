#!/usr/bin/env python3
"""Acceptance criteria — beta dialog tests. Read-only, no code changes."""

from __future__ import annotations

import io
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "https://beta.genesis-ai-engine.com"
TIMEOUT = 90

_SERVICE_PHRASES = (
    "понятно.",
    "записал.",
    "записал:",
    "ясно.",
    "слышу вас.",
    "спасибо, теперь картина яснее.",
    "теперь уже можно что-то предложить.",
    "тогда я бы рекомендовал",
    "на связи. давайте поговорим",
    "чем могу помочь сегодня?",
    "расскажите о задаче",
    "универсальный искусственный интеллект",
)

_SALES_MARKERS = (
    "под ключ",
    "/order",
    "650 €",
    "350 €",
    "studio basic",
    "crm",
    "лендинг под ключ",
    "virtus studio",
)

_TEMPLATE_POOL = (
    "отлично, на связи. чем могу помочь",
    "всё хорошо, спасибо! 😊 а у вас как",
    "нормально, спасибо что спросили",
)


@dataclass
class TurnResult:
    user: str
    answer: str
    error: str = ""
    service_hits: list[str] = field(default_factory=list)
    sales_hits: list[str] = field(default_factory=list)
    template_hits: list[str] = field(default_factory=list)
    len_answer: int = 0


@dataclass
class DialogResult:
    name: str
    turns: list[TurnResult] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(self.checks.values()) if self.checks else False


def _analyze(answer: str) -> tuple[list[str], list[str], list[str]]:
    low = answer.lower()
    svc = [p for p in _SERVICE_PHRASES if p in low]
    sales = [p for p in _SALES_MARKERS if p in low]
    tmpl = [p for p in _TEMPLATE_POOL if p in low]
    return svc, sales, tmpl


def _chat(question: str, history: list[dict[str, str]], visitor_id: str) -> TurnResult:
    payload = json.dumps(
        {"question": question, "history": history, "visitor_id": visitor_id},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE.rstrip('/')}/api/public/genesis-ai",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        answer = (body.get("answer") or "").strip()
    except urllib.error.HTTPError as exc:
        return TurnResult(user=question, answer="", error=f"HTTP {exc.code}")
    except Exception as exc:
        return TurnResult(user=question, answer="", error=str(exc))
    svc, sales, tmpl = _analyze(answer)
    return TurnResult(
        user=question,
        answer=answer,
        service_hits=svc,
        sales_hits=sales,
        template_hits=tmpl,
        len_answer=len(answer),
    )


def _run_dialog(name: str, messages: list[str], visitor_id: str) -> DialogResult:
    dr = DialogResult(name=name)
    history: list[dict[str, str]] = []
    for msg in messages:
        tr = _chat(msg, history, visitor_id)
        dr.turns.append(tr)
        if tr.answer and not tr.error:
            history.append({"role": "user", "content": msg})
            history.append({"role": "assistant", "content": tr.answer})
    return dr


def _status() -> dict:
    try:
        with urllib.request.urlopen(f"{BASE}/api/public/genesis-ai/status", timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return {"error": str(exc)}


def evaluate_dialog1(dr: DialogResult) -> None:
    no_service = all(not t.service_hits for t in dr.turns)
    natural = all(t.len_answer >= 12 and not t.error for t in dr.turns)
    no_template = all(not t.template_hits for t in dr.turns)
    # memory: turn 3+ should reference Vector/assistant context from prior turns
    memory_ok = True
    if len(dr.turns) >= 3:
        a3 = dr.turns[2].answer.lower()
        memory_ok = any(w in a3 for w in ("vector", "virtus", "помощник", "я —"))
    dr.checks = {
        "no_service_phrases": no_service,
        "natural_length": natural,
        "no_template_pool": no_template,
        "identity_coherent": memory_ok,
    }
    if not no_service:
        dr.notes.append(f"service hits: {[t.service_hits for t in dr.turns if t.service_hits]}")


def evaluate_dialog2(dr: DialogResult) -> None:
    no_service = all(not t.service_hits for t in dr.turns)
    no_early_sales = not any(t.sales_hits for t in dr.turns[:2])
    consultant = any(
        "направлен" in t.answer.lower() or "иде" in t.answer.lower() or "**1." in t.answer
        for t in dr.turns[1:3]
    )
    explains = any(
        "потому" in t.answer.lower() or "опира" in t.answer.lower() or "честн" in t.answer.lower()
        for t in dr.turns
    )
    budget_ack = any("1000" in t.answer or "€" in t.answer or "евро" in t.answer.lower() for t in dr.turns[3:])
    dr.checks = {
        "no_service_phrases": no_service,
        "no_early_sales": no_early_sales,
        "consultant_ideas": consultant,
        "explains_reasoning": explains,
        "budget_acknowledged": budget_ack,
    }


def evaluate_dialog3(dr: DialogResult) -> None:
    sales_active = any(t.sales_hits for t in dr.turns)
    no_service = all(not t.service_hits for t in dr.turns)
    discusses = any(
        any(w in t.answer.lower() for w in ("сайт", "лендинг", "бот", "заказ", "order"))
        for t in dr.turns
    )
    dr.checks = {
        "product_sales_active": sales_active,
        "discusses_project": discusses,
        "no_service_phrases": no_service,
    }


def evaluate_dialog4(dr: DialogResult) -> None:
    no_service = all(not t.service_hits for t in dr.turns)
    no_sales = all(not t.sales_hits for t in dr.turns)
    empathy = any(
        any(w in t.answer.lower() for w in ("понима", "слышу", "тяжел", "рядом", "нормальн", "жаль"))
        for t in dr.turns
    )
    dr.checks = {
        "no_service_phrases": no_service,
        "no_sales": no_sales,
        "empathy_present": empathy,
    }


def evaluate_dialog5(dr: DialogResult) -> None:
    no_service = all(not t.service_hits for t in dr.turns)
    no_errors = all(not t.error for t in dr.turns)
    # topic: coffee shop thread
    topic_words = ("кофе", "кафе", "бизнес", "бюджет", "евро", "€")
    topic_hits = sum(
        1 for t in dr.turns if any(w in t.answer.lower() for w in topic_words)
    )
    topic_ok = topic_hits >= 3
    # repetition: last answer shouldn't equal earlier verbatim
    answers = [t.answer.strip().lower() for t in dr.turns if t.answer]
    repeat = len(answers) != len(set(answers))
    dr.checks = {
        "no_service_phrases": no_service,
        "no_errors": no_errors,
        "topic_retained": topic_ok,
        "no_exact_repeats": not repeat,
    }


def _long_context_messages() -> list[str]:
    return [
        "Привет, хочу открыть небольшую кофейню",
        "В Берлине",
        "Бюджет около 5000 евро",
        "Какие риски?",
        "А если бюджет только 2000?",
        "Что насчёт доставки кофе?",
        "Нужен ли сайт сразу?",
        "Сколько человек в команде минимум?",
        "Как привлечь первых клиентов?",
        "Соцсети или карты?",
        "А если аренда дорогая?",
        "Можно начать с coffee to go?",
        "Сколько месяцев до окупаемости — грубо?",
        "Что бы ты сделал на моём месте?",
        "Спасибо, это полезно",
        "Ещё один вопрос: нужна ли касса?",
        "Итого — с чего начать в первую неделю?",
    ]


def print_dialog(dr: DialogResult) -> None:
    print(f"\n{'='*60}")
    print(f"DIALOG: {dr.name}")
    print(f"PASS: {dr.passed}")
    for k, v in dr.checks.items():
        print(f"  [{('OK' if v else 'FAIL')}] {k}")
    for note in dr.notes:
        print(f"  note: {note}")
    for i, t in enumerate(dr.turns, 1):
        print(f"\n--- Turn {i} ---")
        print(f"USER: {t.user}")
        if t.error:
            print(f"ERROR: {t.error}")
        else:
            print(f"ASSISTANT ({t.len_answer} chars): {t.answer}")
            if t.service_hits:
                print(f"  SERVICE: {t.service_hits}")
            if t.sales_hits:
                print(f"  SALES: {t.sales_hits}")
            if t.template_hits:
                print(f"  TEMPLATE: {t.template_hits}")


def main() -> int:
    print("=== ACCEPTANCE: beta.genesis-ai-engine.com ===")
    st = _status()
    print(f"status: brain={st.get('brain_version')} llm={st.get('llm_configured')} cloud={st.get('workforce',{}).get('cloud_employees_ready')}")
    if st.get("error"):
        print(f"status error: {st['error']}")

    d1 = _run_dialog(
        "1 — обычное общение",
        ["Привет", "Как дела?", "Кто ты?", "Что умеешь?"],
        "accept-d1",
    )
    evaluate_dialog1(d1)

    d2 = _run_dialog(
        "2 — консультация",
        [
            "Хочу открыть бизнес.",
            "Посоветуй идеи.",
            "Почему именно эти?",
            "У меня бюджет 1000 евро.",
        ],
        "accept-d2",
    )
    evaluate_dialog2(d2)

    d3 = _run_dialog(
        "3 — заказ продукта",
        ["Мне нужен сайт.", "Нужен лендинг.", "Хочу заказать чат-бота."],
        "accept-d3",
    )
    evaluate_dialog3(d3)

    d4 = _run_dialog(
        "4 — эмоциональный",
        ["Мне грустно.", "Я устал.", "Я не знаю что делать."],
        "accept-d4",
    )
    evaluate_dialog4(d4)

    d5 = _run_dialog("5 — длинный контекст", _long_context_messages(), "accept-d5")
    evaluate_dialog5(d5)

    dialogs = [d1, d2, d3, d4, d5]
    for dr in dialogs:
        print_dialog(dr)

    passed = sum(1 for d in dialogs if d.passed)
    print(f"\n{'='*60}")
    print(f"SUMMARY: {passed}/{len(dialogs)} dialogs passed")
    for dr in dialogs:
        print(f"  {'PASS' if dr.passed else 'FAIL'} — {dr.name}")
    return 0 if passed == len(dialogs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
