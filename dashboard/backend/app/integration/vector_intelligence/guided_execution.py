"""Guided Execution — GMB setup with Energy Budget (one evening win per session).

When the user says they cannot do it alone, Vector becomes a guide:
one micro-step → «Готово» → stop for today → next visit continues.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.integration.project_platform.journey_state import (
    extract_city_label,
    extract_company_name,
)
from app.integration.vector_intelligence.decision_intelligence import (
    evaluate_company_situation,
)

_GMB_URL = "https://business.google.com/"

_GUIDED_TRIGGER = re.compile(
    r"(?:"
    r"покажи\s+(?:как|мне|по)|"
    r"как\s+для\s+тупого|"
    r"по\s+шагам|"
    r"не\s+умею|"
    r"не\s+знаю\s+как|"
    r"возьми\s+меня|"
    r"проведи\s+меня|"
    r"продолж|"
    r"show\s+me\s+how"
    r")",
    re.I,
)

_DONE_SIGNAL = re.compile(
    r"^(?:готово|сделал|сделано|done)(?:[\s!.,]|$)",
    re.I,
)

_GMB_CONTEXT = re.compile(r"google\s+business|gmb|бизнес[\s-]?профил", re.I)


@dataclass
class GuidedSession:
    task_id: str = "gmb_setup"
    step_index: int = 0
    company: str = ""
    city: str = ""
    completed: bool = False
    evening_paused: bool = False

    @property
    def total_steps(self) -> int:
        return len(_EVENING_SLICES)


def try_guided_execution_route(
    text: str,
    *,
    visitor_id: str,
    memory_dir: Path,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any] | None:
    """Return chat dict when guiding GMB setup, or None."""
    goal = (text or "").strip()
    if not goal or not visitor_id:
        return None

    session = _load_session(memory_dir, visitor_id)
    combined = _combined_dialogue(goal, history)

    if session and session.completed:
        _clear_session(memory_dir, visitor_id)
        session = None

    if session and session.evening_paused:
        if _DONE_SIGNAL.match(goal):
            return _already_enough_today(session)
        session.evening_paused = False
        _save_session(memory_dir, visitor_id, session)
        return _evening_slice_response(session)

    if session and _DONE_SIGNAL.match(goal):
        return _advance_evening(memory_dir, visitor_id, session)

    if session and not _GUIDED_TRIGGER.search(goal):
        return _remind_session(session)

    if _GUIDED_TRIGGER.search(goal) or (session and not session.completed):
        if not session:
            if not _should_start_gmb_guide(combined, history):
                return None
            session = _new_gmb_session(combined)
            _save_session(memory_dir, visitor_id, session)
        return _evening_slice_response(session)

    return None


def _should_start_gmb_guide(combined: str, history: list[dict[str, str]] | None) -> bool:
    if _GMB_CONTEXT.search(combined):
        return True
    if history:
        for msg in reversed(history):
            if msg.get("role") == "assistant" and _GMB_CONTEXT.search(msg.get("content") or ""):
                return True
    brief = evaluate_company_situation(combined)
    if brief and not brief.website_first and brief.recommended_focus == "presence_first":
        return True
    return False


def _new_gmb_session(combined: str) -> GuidedSession:
    company = extract_company_name(combined) or "вашу компанию"
    city = extract_city_label(combined) or "ваш город"
    return GuidedSession(company=company, city=city, step_index=0)


def _advance_evening(memory_dir: Path, visitor_id: str, session: GuidedSession) -> dict[str, Any]:
    finished = _EVENING_SLICES[session.step_index]
    next_index = session.step_index + 1
    if next_index >= session.total_steps:
        session.completed = True
        _clear_session(memory_dir, visitor_id)
        return _completion_response(session, finished_slice=finished)
    session.step_index = next_index
    session.evening_paused = True
    _save_session(memory_dir, visitor_id, session)
    return _evening_stop_response(session, finished_slice=finished)


def _already_enough_today(session: GuidedSession) -> dict[str, Any]:
    nxt = _EVENING_SLICES[session.step_index]
    return {
        "answer": (
            "На сегодня уже достаточно — вы молодец.\n\n"
            f"Завтра продолжим: {nxt['tomorrow_teaser']}\n\n"
            "Отдохните. Я сохранил, где мы остановились."
        ),
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "context": {
            "guided_execution": True,
            "evening_paused": True,
            "step": session.step_index + 1,
        },
    }


def _remind_session(session: GuidedSession) -> dict[str, Any]:
    sl = _EVENING_SLICES[session.step_index]
    return _chat_dict(
        answer=(
            f"Мы вместе — **{sl['title']}**.\n\n"
            f"Сегодня: {sl['today_action'](session.company, session.city)}\n\n"
            "Когда сделаете — нажмите **Готово**. На сегодня больше ничего не нужно."
        ),
        session=session,
        slice_row=sl,
        include_done=True,
    )


def _evening_slice_response(session: GuidedSession) -> dict[str, Any]:
    sl = _EVENING_SLICES[session.step_index]
    company = session.company
    city = session.city
    lines = ["Делаем Google Business вместе."]
    if sl.get("yesterday_recap"):
        lines.extend(["", sl["yesterday_recap"], ""])
    lines.extend(
        [
            f"**Сегодня — одно действие:**",
            f"✓ {sl['today_action'](company, city)}",
            "",
            "На сегодня — только это. Когда сделаете, нажмите **Готово**.",
            "Завтра продолжим отсюда.",
        ]
    )
    return _chat_dict(
        answer="\n".join(lines),
        session=session,
        slice_row=sl,
        include_done=True,
    )


def _evening_stop_response(session: GuidedSession, *, finished_slice: dict[str, Any]) -> dict[str, Any]:
    nxt = _EVENING_SLICES[session.step_index]
    win = finished_slice["win_label"](session.company, session.city)
    return {
        "answer": (
            f"Отлично. **На сегодня достаточно** — {win}.\n\n"
            f"Завтра продолжим: {nxt['tomorrow_teaser']}\n\n"
            "Хорошо, что вы сегодня открыли Vector. Увидимся завтра."
        ),
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "context": {
            "guided_execution": True,
            "evening_paused": True,
            "evening_win": True,
            "step": session.step_index + 1,
            "total_steps": session.total_steps,
            "company": session.company,
            "city": session.city,
        },
    }


def _completion_response(session: GuidedSession, *, finished_slice: dict[str, Any]) -> dict[str, Any]:
    company = session.company
    city = session.city
    win = finished_slice["win_label"](company, city)
    answer = (
        f"Готово — **{win}**.\n\n"
        f"✓ {company} оформлена в Google для региона {city}\n"
        "✓ Клиенты смогут найти вас в поиске и на карте\n"
        "✓ Следующий шаг — собрать первые отзывы\n\n"
        "Обычно это проще, чем кажется до начала."
    )
    return {
        "answer": answer,
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": _GMB_URL,
        "cta_label": "Открыть профиль",
        "cta_actions": [
            {"href": _GMB_URL, "label": "Открыть Google Business", "group": "artifacts"},
        ],
        "context": {
            "guided_execution": True,
            "task_id": session.task_id,
            "completed": True,
            "company": company,
            "city": city,
        },
    }


def _chat_dict(
    *,
    answer: str,
    session: GuidedSession,
    slice_row: dict[str, Any],
    include_done: bool,
) -> dict[str, Any]:
    actions: list[dict[str, str]] = []
    link = slice_row.get("link")
    if link:
        actions.append(
            {"href": link, "label": slice_row.get("link_label", "Открыть"), "group": "artifacts"},
        )
    if include_done:
        actions.append(
            {"href": "#action:Готово", "label": "Готово — на сегодня хватит", "group": "next"},
        )
    return {
        "answer": answer,
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": link,
        "cta_label": slice_row.get("link_label"),
        "cta_actions": actions,
        "context": {
            "guided_execution": True,
            "energy_budget": True,
            "task_id": session.task_id,
            "step": session.step_index + 1,
            "total_steps": session.total_steps,
            "company": session.company,
            "city": session.city,
        },
    }


def _combined_dialogue(goal: str, history: list[dict[str, str]] | None) -> str:
    chunks = [goal]
    if history:
        for msg in history:
            if msg.get("role") == "user":
                chunks.append((msg.get("content") or "").strip())
    return "\n".join(c for c in chunks if c)


_EVENING_SLICES: list[dict[str, Any]] = [
    {
        "title": "Открыть страницу",
        "yesterday_recap": None,
        "today_action": lambda company, city: "откройте business.google.com (кнопка ниже)",
        "win_label": lambda company, city: "вы открыли Google Business",
        "tomorrow_teaser": "войдём в Google-аккаунт",
        "link": _GMB_URL,
        "link_label": "Открыть business.google.com",
    },
    {
        "title": "Войти в аккаунт",
        "yesterday_recap": "Вчера мы открыли Google Business.",
        "today_action": lambda company, city: "войдите в Google-аккаунт, которым пользуетесь для работы",
        "win_label": lambda company, city: "вы вошли в аккаунт",
        "tomorrow_teaser": f"найдём или создадим компанию",
        "link": _GMB_URL,
        "link_label": "Продолжить в Google Business",
    },
    {
        "title": "Найти компанию",
        "yesterday_recap": "Вчера мы вошли в Google-аккаунт.",
        "today_action": lambda company, city: f"в поиске введите **{company}** — или «Добавить компанию»",
        "win_label": lambda company, city: f"вы нашли или создали {company}",
        "tomorrow_teaser": "укажем город и адрес",
        "link": _GMB_URL,
        "link_label": "Продолжить в Google Business",
    },
    {
        "title": "Город и адрес",
        "yesterday_recap": "Вчера мы нашли компанию в Google.",
        "today_action": lambda company, city: f"укажите город **{city}** и адрес или зону выезда",
        "win_label": lambda company, city: "вы указали адрес",
        "tomorrow_teaser": "добавим категорию и телефон",
        "link": _GMB_URL,
        "link_label": "Продолжить в Google Business",
    },
    {
        "title": "Подтверждение",
        "yesterday_recap": "Вчера мы указали адрес.",
        "today_action": lambda company, city: "выберите способ подтверждения (открытка, звонок или email)",
        "win_label": lambda company, city: "вы запустили подтверждение профиля",
        "tomorrow_teaser": "профиль будет виден после проверки Google",
        "link": _GMB_URL,
        "link_label": "Продолжить в Google Business",
    },
]


def _session_path(memory_dir: Path, visitor_id: str) -> Path:
    root = memory_dir / "guided_execution"
    root.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w\-]", "_", visitor_id.strip()[:64])
    return root / f"{safe}.json"


def _load_session(memory_dir: Path, visitor_id: str) -> GuidedSession | None:
    path = _session_path(memory_dir, visitor_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if "evening_paused" not in data:
            data["evening_paused"] = False
        return GuidedSession(**data)
    except (json.JSONDecodeError, OSError, TypeError):
        return None


def _save_session(memory_dir: Path, visitor_id: str, session: GuidedSession) -> None:
    path = _session_path(memory_dir, visitor_id)
    path.write_text(json.dumps(asdict(session), ensure_ascii=False, indent=2), encoding="utf-8")


def _clear_session(memory_dir: Path, visitor_id: str) -> None:
    path = _session_path(memory_dir, visitor_id)
    if path.is_file():
        path.unlink(missing_ok=True)
