"""
Genesis Memory Layer — long-term user & company memory (not just chat history).

Persists facts across sessions when visitor_id is provided.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent.parent.parent / "memory"
_NAME_RE = re.compile(r"меня\s+зовут\s+([A-Za-zА-Яа-яЁё\-]+)", re.I)
_AGE_RE = re.compile(r"мне\s+(\d{1,2})\s*(?:лет|года|год)?", re.I)
_PROJECT_RE = re.compile(
    r"(?:запустил[иа]?|делаем|работаем\s+над|проект)\s+(.{3,80})",
    re.I,
)
_MILESTONE_KEYWORDS = (
    ("public launch", "Запущен Public Launch"),
    ("marketing lab", "Работа над Marketing Lab"),
    ("ai sales", "Разработка AI Sales"),
    ("factory", "Проект в Factory"),
    ("studio", "Использует Genesis Studio"),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GenesisMemoryLayer:
    """File-backed memory — foundation for lifelong user relationships."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._root = (memory_dir or _DEFAULT_MEMORY) / "genesis_brain" / "users"
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, visitor_id: str) -> Path:
        safe = re.sub(r"[^\w\-]", "_", visitor_id)[:64] or "anonymous"
        return self._root / f"{safe}.json"

    def load(self, visitor_id: str) -> dict[str, Any]:
        path = self._path(visitor_id)
        if not path.is_file():
            return {
                "visitor_id": visitor_id,
                "name": None,
                "facts": [],
                "milestones": [],
                "visit_count": 0,
            }
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            pass
        return {"visitor_id": visitor_id, "name": None, "facts": [], "milestones": [], "visit_count": 0}

    def save(self, visitor_id: str, data: dict[str, Any]) -> None:
        data["visitor_id"] = visitor_id
        data["updated_at"] = _utc_now()
        path = self._path(visitor_id)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def build_context_block(self, visitor_id: str) -> str:
        data = self.load(visitor_id)
        lines: list[str] = []
        inf = data.get("inferences") or {}
        if inf.get("long_term_goals"):
            lines.append("- Долгосрочные цели: " + ", ".join(inf["long_term_goals"][:5]))
        if inf.get("core_values"):
            lines.append("- Ценности: " + ", ".join(inf["core_values"][:5]))
        if inf.get("communication_style"):
            lines.append(f"- Стиль общения: {inf['communication_style']}")
        if inf.get("preferred_depth"):
            lines.append(f"- Предпочитает: {inf['preferred_depth']}")
        if inf.get("risk_profile"):
            lines.append(f"- Профиль риска: {inf['risk_profile']}")
        if data.get("name"):
            lines.append(f"- Имя: {data['name']}")
        if data.get("user_age"):
            lines.append(f"- Возраст: {data['user_age']} лет")
        for m in (data.get("milestones") or [])[-8:]:
            if isinstance(m, str):
                lines.append(f"- Веха: {m}")
        for f in (data.get("facts") or [])[-12:]:
            if isinstance(f, dict) and f.get("text"):
                lines.append(f"- {f['text']}")
            elif isinstance(f, str):
                lines.append(f"- {f}")
        if not lines:
            return ""
        return "\n".join(lines)

    def observe_messages(self, visitor_id: str, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Extract facts from history and persist."""
        data = self.load(visitor_id)
        facts: list[dict[str, str]] = list(data.get("facts") or [])
        milestones: list[str] = list(data.get("milestones") or [])
        name = data.get("name")

        for m in messages:
            if m.get("role") != "user":
                continue
            content = (m.get("content") or "").strip()
            if not content:
                continue
            nm = _NAME_RE.search(content)
            if nm:
                name = nm.group(1).strip()
            age_m = _AGE_RE.search(content)
            if age_m:
                data["user_age"] = int(age_m.group(1))
                fact_text = f"Возраст: {age_m.group(1)} лет"
                if not any(
                    isinstance(f, dict) and f.get("text") == fact_text for f in facts
                ):
                    facts.append({"at": _utc_now(), "text": fact_text})
            low = content.lower()
            for key, label in _MILESTONE_KEYWORDS:
                if key in low and label not in milestones:
                    milestones.append(label)
            proj = _PROJECT_RE.search(content)
            if proj:
                fact_text = f"Проект/задача: {proj.group(1).strip()}"
                if not any(f.get("text") == fact_text for f in facts if isinstance(f, dict)):
                    facts.append({"at": _utc_now(), "text": fact_text})

        data["name"] = name
        data["facts"] = facts[-50:]
        data["milestones"] = milestones[-20:]
        self.save(visitor_id, data)
        return data

    def record_exchange(
        self,
        visitor_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        data = self.observe_messages(visitor_id, [{"role": "user", "content": user_message}])
        exchanges: list[dict[str, str]] = list(data.get("recent_exchanges") or [])
        exchanges.append(
            {
                "at": _utc_now(),
                "user": user_message[:500],
                "assistant": assistant_message[:500],
            }
        )
        data["recent_exchanges"] = exchanges[-30:]
        data["visit_count"] = int(data.get("visit_count") or 0) + 1
        self.save(visitor_id, data)

    def get_inferences(self, visitor_id: str) -> dict[str, Any]:
        data = self.load(visitor_id)
        return dict(data.get("inferences") or {})

    def update_inferences(
        self,
        visitor_id: str,
        thinking: Any,
        state: Any,
    ) -> None:
        """Persist conclusions about the person — not raw messages."""
        data = self.load(visitor_id)
        inf: dict[str, Any] = dict(data.get("inferences") or {})

        if thinking.real_goal and "финансов" in thinking.real_goal:
            goals = list(inf.get("long_term_goals") or [])
            if "финансовая свобода" not in goals:
                goals.append("финансовая свобода")
            inf["long_term_goals"] = goals[-8:]

        if thinking.emotional_state in ("сомнение", "тревога"):
            inf["risk_profile"] = "осторожный"
        elif thinking.emotional_state == "надежда":
            inf["risk_profile"] = "амбициозный"

        if state.life_goal == "financial_independence":
            values = list(inf.get("core_values") or [])
            if "финансовая независимость" not in values:
                values.append("финансовая независимость")
            inf["core_values"] = values[-8:]

        if thinking.best_response_strategy and "глубин" in thinking.best_response_strategy:
            inf["preferred_depth"] = "deep"

        data["inferences"] = inf
        self.save(visitor_id, data)

    def recall_name(self, visitor_id: str, messages: list[dict[str, str]]) -> str | None:
        data = self.observe_messages(visitor_id, messages)
        return data.get("name")
