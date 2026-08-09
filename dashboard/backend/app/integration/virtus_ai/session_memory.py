"""Session memory for Virtus AI (file-backed stub)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _root() -> Path:
    # dashboard/backend/app/integration/virtus_ai → dashboard/backend
    return Path(__file__).resolve().parents[3] / "data" / "virtus_ai_sessions"


def _path(client_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (client_id or "anon"))[:80]
    return _root() / f"{safe}.json"


def load_session(client_id: str) -> dict[str, Any]:
    p = _path(client_id)
    if not p.is_file():
        return {"client_id": client_id, "turns": [], "checklist": {}, "last_session": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"client_id": client_id, "turns": [], "checklist": {}, "last_session": {}}


def save_session(client_id: str, data: dict[str, Any]) -> dict[str, Any]:
    p = _path(client_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = dict(data)
    data["client_id"] = client_id
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def append_turn(client_id: str, role: str, text: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    sess = load_session(client_id)
    turns = list(sess.get("turns") or [])
    turns.append(
        {
            "role": role,
            "text": text,
            "at": datetime.now(timezone.utc).isoformat(),
            "meta": meta or {},
        }
    )
    sess["turns"] = turns[-40:]
    sess["last_session"] = {
        "summary": (text[:120] if role == "assistant" else sess.get("last_session", {}).get("summary")),
        "at": datetime.now(timezone.utc).isoformat(),
    }
    return save_session(client_id, sess)
