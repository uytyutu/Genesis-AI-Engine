"""Chat sessions — per-thread context separate from visitor long-term memory."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_id(raw: str, *, max_len: int = 64) -> str:
    return re.sub(r"[^\w\-]", "_", raw)[:max_len] or "anonymous"


def _auto_title(text: str, *, max_len: int = 48) -> str:
    t = " ".join((text or "").strip().split())
    if not t:
        return "Новый чат"
    t = re.sub(r"^[\W_]+", "", t)
    if len(t) <= max_len:
        return t[0].upper() + t[1:] if t else "Новый чат"
    cut = t[:max_len].rsplit(" ", 1)[0] or t[:max_len]
    return cut.rstrip(".,!?;:") + "…"


class ChatSessionStore:
    """Level 1–2: thread messages + conversation_state. Level 3 stays in visitor profile."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        root = memory_dir or _DEFAULT_MEMORY
        self._sessions = root / "genesis_brain" / "sessions"
        self._index = root / "genesis_brain" / "session_index"
        self._sessions.mkdir(parents=True, exist_ok=True)
        self._index.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self._sessions / f"{_safe_id(session_id)}.json"

    def _index_path(self, visitor_id: str) -> Path:
        return self._index / f"{_safe_id(visitor_id)}.json"

    def create(self, visitor_id: str, *, title: str = "Новый чат") -> dict[str, Any]:
        sid = str(uuid.uuid4())
        now = _utc_now()
        row = {
            "session_id": sid,
            "visitor_id": visitor_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "pinned": False,
            "messages": [],
            "conversation_state": {},
        }
        self._session_path(sid).write_text(
            json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._upsert_index(visitor_id, sid, title=title, updated_at=now, preview="")
        return row

    def get(self, session_id: str) -> dict[str, Any] | None:
        path = self._session_path(session_id)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, OSError):
            return None

    def save(self, session: dict[str, Any]) -> None:
        sid = session.get("session_id")
        if not sid:
            return
        session["updated_at"] = _utc_now()
        self._session_path(sid).write_text(
            json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        vid = session.get("visitor_id") or "anonymous"
        preview = ""
        for m in reversed(session.get("messages") or []):
            if m.get("role") == "user":
                preview = (m.get("content") or "")[:120]
                break
        self._upsert_index(
            vid,
            sid,
            title=session.get("title") or "Новый чат",
            updated_at=session["updated_at"],
            preview=preview,
            pinned=bool(session.get("pinned")),
            created_at=session.get("created_at"),
        )

    def list_for_visitor(self, visitor_id: str) -> list[dict[str, Any]]:
        path = self._index_path(visitor_id)
        if not path.is_file():
            return []
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        if not isinstance(rows, list):
            return []
        out = [r for r in rows if isinstance(r, dict)]
        out.sort(
            key=lambda r: (
                not bool(r.get("pinned")),
                r.get("updated_at") or "",
            ),
            reverse=True,
        )
        return out

    def delete(self, session_id: str, visitor_id: str) -> bool:
        path = self._session_path(session_id)
        if path.is_file():
            path.unlink()
        idx_path = self._index_path(visitor_id)
        if not idx_path.is_file():
            return True
        try:
            rows = json.loads(idx_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return True
        if not isinstance(rows, list):
            return True
        rows = [r for r in rows if r.get("session_id") != session_id]
        idx_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        return True

    def set_pinned(self, session_id: str, visitor_id: str, pinned: bool) -> dict[str, Any] | None:
        session = self.get(session_id)
        if not session or session.get("visitor_id") != visitor_id:
            return None
        session["pinned"] = pinned
        self.save(session)
        return session

    def rename(self, session_id: str, visitor_id: str, title: str) -> dict[str, Any] | None:
        session = self.get(session_id)
        if not session or session.get("visitor_id") != visitor_id:
            return None
        t = (title or "").strip() or "Новый чат"
        session["title"] = t[:80]
        self.save(session)
        return session

    def append_messages(
        self,
        session_id: str,
        *,
        user: str,
        assistant: str,
        auto_title_from: str | None = None,
    ) -> None:
        session = self.get(session_id)
        if not session:
            return
        msgs: list[dict[str, str]] = list(session.get("messages") or [])
        if user.strip():
            msgs.append({"role": "user", "content": user.strip(), "at": _utc_now()})
        if assistant.strip():
            msgs.append({"role": "assistant", "content": assistant.strip(), "at": _utc_now()})
        session["messages"] = msgs[-80:]
        if auto_title_from and (session.get("title") or "Новый чат") == "Новый чат":
            session["title"] = _auto_title(auto_title_from)
        self.save(session)

    def get_conversation_state(self, session_id: str) -> dict[str, Any]:
        session = self.get(session_id)
        if not session:
            return {}
        return dict(session.get("conversation_state") or {})

    def set_conversation_state(self, session_id: str, state: dict[str, Any]) -> None:
        session = self.get(session_id)
        if not session:
            return
        session["conversation_state"] = state
        self.save(session)

    def _upsert_index(
        self,
        visitor_id: str,
        session_id: str,
        *,
        title: str,
        updated_at: str,
        preview: str = "",
        pinned: bool = False,
        created_at: str | None = None,
    ) -> None:
        path = self._index_path(visitor_id)
        rows: list[dict[str, Any]] = []
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    rows = [r for r in raw if isinstance(r, dict)]
            except (json.JSONDecodeError, OSError):
                rows = []
        found = False
        for r in rows:
            if r.get("session_id") == session_id:
                r["title"] = title
                r["updated_at"] = updated_at
                r["preview"] = preview
                r["pinned"] = pinned
                if created_at:
                    r["created_at"] = created_at
                found = True
                break
        if not found:
            rows.append(
                {
                    "session_id": session_id,
                    "title": title,
                    "updated_at": updated_at,
                    "created_at": created_at or updated_at,
                    "preview": preview,
                    "pinned": pinned,
                }
            )
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
