"""Email contact status — Active / Unsubscribed / Bounced / Blocked (CRM lite).

Used by Support «Unsubscribe» and Lead Engine Quality Gate so marketing
outreach never re-mails opted-out addresses. History stays in Support.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

EmailStatus = Literal["active", "unsubscribed", "bounced", "blocked"]

_VALID: frozenset[str] = frozenset({"active", "unsubscribed", "bounced", "blocked"})
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_email(raw: str | None) -> str:
    text = str(raw or "").strip().lower()
    m = _EMAIL_RE.search(text)
    return (m.group(0) if m else text).strip().lower()


class EmailContactStatusService:
    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._memory.mkdir(parents=True, exist_ok=True)
        self._path = self._memory / "email_contact_status.json"

    def _load(self) -> dict[str, Any]:
        if not self._path.is_file():
            return {"version": 1, "contacts": {}}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"version": 1, "contacts": {}}
        if not isinstance(data, dict):
            return {"version": 1, "contacts": {}}
        contacts = data.get("contacts")
        if not isinstance(contacts, dict):
            data["contacts"] = {}
        return data

    def _save(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, email: str) -> dict[str, Any] | None:
        key = normalize_email(email)
        if not key or "@" not in key:
            return None
        row = self._load().get("contacts", {}).get(key)
        return dict(row) if isinstance(row, dict) else None

    def status_of(self, email: str) -> EmailStatus:
        row = self.get(email)
        if not row:
            return "active"
        st = str(row.get("status") or "active").lower()
        return st if st in _VALID else "active"  # type: ignore[return-value]

    def is_marketing_blocked(self, email: str) -> bool:
        return self.status_of(email) in ("unsubscribed", "bounced", "blocked")

    def set_status(
        self,
        email: str,
        status: str,
        *,
        source: str = "manual",
        note: str = "",
        thread_id: str = "",
    ) -> dict[str, Any]:
        key = normalize_email(email)
        if not key or "@" not in key:
            raise ValueError("invalid_email")
        st = str(status or "").strip().lower()
        if st not in _VALID:
            raise ValueError("invalid_status")
        data = self._load()
        contacts: dict[str, Any] = data.setdefault("contacts", {})
        prev = contacts.get(key) if isinstance(contacts.get(key), dict) else {}
        row = {
            "email": key,
            "status": st,
            "source": (source or "manual").strip() or "manual",
            "note": (note or "").strip(),
            "thread_id": (thread_id or "").strip() or prev.get("thread_id") or "",
            "updated_at": utc_now(),
            "created_at": prev.get("created_at") or utc_now(),
        }
        contacts[key] = row
        data["contacts"] = contacts
        self._save(data)
        return row

    def mark_unsubscribed(
        self,
        email: str,
        *,
        source: str = "support",
        thread_id: str = "",
        note: str = "",
    ) -> dict[str, Any]:
        return self.set_status(
            email,
            "unsubscribed",
            source=source,
            thread_id=thread_id,
            note=note or "Do not send marketing / outreach emails",
        )


def suppress_outreach_leads_for_email(memory_dir: Path, email: str) -> int:
    """Tag matching opportunities so hunt/send skip them (meta.do_not_contact)."""
    key = normalize_email(email)
    if not key:
        return 0
    path = memory_dir / "opportunities.jsonl"
    if not path.is_file():
        return 0
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    touched = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            out.append(line)
            continue
        contact = normalize_email(str(row.get("contact") or ""))
        if contact == key:
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            meta = dict(meta)
            meta["do_not_contact"] = True
            meta["email_status"] = "unsubscribed"
            meta["skip_outreach"] = True
            row["meta"] = meta
            touched += 1
        out.append(json.dumps(row, ensure_ascii=False))
    if touched:
        path.write_text("\n".join(out) + ("\n" if out else ""), encoding="utf-8")
    return touched
