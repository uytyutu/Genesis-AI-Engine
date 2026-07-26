"""Forever outreach suppress — never re-email an address Virtus already mailed.

Survives lead resets / opportunity purges. File is never deleted by reset_old_base.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ENGINE_ID = "outreach_sent_forever_v1"
FOREVER_FILENAME = "outreach_sent_forever.json"

_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_email(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    m = _EMAIL_RE.search(raw)
    return (m.group(0) if m else raw).strip().lower()


def normalize_host(url_or_host: str | None) -> str:
    raw = (url_or_host or "").strip().lower()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    try:
        host = urlparse(raw).netloc.lower()
    except Exception:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host.split(":")[0]


def _empty() -> dict[str, Any]:
    return {
        "version": 1,
        "engine": ENGINE_ID,
        "emails": {},
        "hosts": {},
        "updated_at": None,
    }


class OutreachSentForever:
    """Durable sent ledger under memory_dir / outreach_sent_forever.json."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = Path(memory_dir) if memory_dir else Path(__file__).resolve().parent.parent / "memory"
        self._memory.mkdir(parents=True, exist_ok=True)
        self._path = self._memory / FOREVER_FILENAME

    @property
    def path(self) -> Path:
        return self._path

    def _load(self) -> dict[str, Any]:
        if not self._path.is_file():
            return _empty()
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return _empty()
        if not isinstance(data, dict):
            return _empty()
        data.setdefault("emails", {})
        data.setdefault("hosts", {})
        if not isinstance(data["emails"], dict):
            data["emails"] = {}
        if not isinstance(data["hosts"], dict):
            data["hosts"] = {}
        return data

    def _save(self, data: dict[str, Any]) -> None:
        data["version"] = 1
        data["engine"] = ENGINE_ID
        data["updated_at"] = _now()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def was_sent(
        self,
        *,
        email: str | None = None,
        website_url: str | None = None,
    ) -> tuple[bool, str]:
        data = self._load()
        em = normalize_email(email)
        if em and em in data["emails"]:
            return True, "email_ever_sent"
        host = normalize_host(website_url)
        if host and host in data["hosts"]:
            return True, "host_ever_sent"
        return False, ""

    def record_sent(
        self,
        *,
        email: str | None = None,
        website_url: str | None = None,
        source: str = "outreach",
        opportunity_id: str = "",
    ) -> dict[str, Any]:
        em = normalize_email(email)
        host = normalize_host(website_url)
        if not em and not host:
            return {"ok": False, "error": "email_or_host_required"}
        data = self._load()
        stamp = _now()
        meta = {
            "first_sent_at": stamp,
            "last_sent_at": stamp,
            "source": (source or "outreach")[:80],
            "opportunity_id": (opportunity_id or "")[:80],
        }
        if em:
            prev = data["emails"].get(em) if isinstance(data["emails"].get(em), dict) else None
            row = dict(prev) if prev else dict(meta)
            row["last_sent_at"] = stamp
            row["source"] = meta["source"]
            if opportunity_id:
                row["opportunity_id"] = meta["opportunity_id"]
            if not row.get("first_sent_at"):
                row["first_sent_at"] = stamp
            data["emails"][em] = row
        if host:
            prev_h = data["hosts"].get(host) if isinstance(data["hosts"].get(host), dict) else None
            row_h = dict(prev_h) if prev_h else dict(meta)
            row_h["last_sent_at"] = stamp
            row_h["source"] = meta["source"]
            if opportunity_id:
                row_h["opportunity_id"] = meta["opportunity_id"]
            if not row_h.get("first_sent_at"):
                row_h["first_sent_at"] = stamp
            data["hosts"][host] = row_h
        self._save(data)
        return {
            "ok": True,
            "email": em or None,
            "host": host or None,
            "emails_total": len(data["emails"]),
            "hosts_total": len(data["hosts"]),
        }

    def ingest_row(self, row: dict[str, Any], *, source: str = "bootstrap") -> bool:
        """If row looks sent/contacted, record email+host. Returns True if recorded."""
        status = str(row.get("status") or "").strip().lower()
        outreach = str(row.get("outreach_status") or "").strip().lower()
        if outreach not in ("sent", "contacted") and status not in (
            "contacted",
            "won",
            "replied",
            "qualified",
        ):
            # contact_history lines use email/domain keys without outreach_status
            if "email" not in row and "contact" not in row:
                return False
            if outreach or status:
                return False
        email = normalize_email(str(row.get("contact") or row.get("email") or ""))
        host = normalize_host(
            str(row.get("website_url") or row.get("domain") or row.get("website") or "")
        )
        if not email and not host:
            return False
        # contact_history always counts as contacted
        if "domain" in row and "at" in row and not outreach and not status:
            self.record_sent(
                email=email,
                website_url=host,
                source=source,
                opportunity_id=str(row.get("id") or ""),
            )
            return True
        if outreach in ("sent", "contacted") or status in (
            "contacted",
            "won",
            "replied",
            "qualified",
        ):
            self.record_sent(
                email=email,
                website_url=host or str(row.get("website_url") or ""),
                source=source,
                opportunity_id=str(row.get("id") or ""),
            )
            return True
        return False

    def ingest_jsonl(self, path: Path, *, source: str) -> int:
        if not path.is_file():
            return 0
        n = 0
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict) and self.ingest_row(row, source=source):
                    n += 1
        except OSError:
            return n
        return n

    def bootstrap_from_memory(self) -> dict[str, Any]:
        """Scan live + archived lead files once so history before this module still blocks."""
        before = self._load()
        before_n = len(before.get("emails") or {})
        added = 0
        roots: list[Path] = [self._memory]
        # Legacy / alternate memory roots used by older runs
        alt = Path(__file__).resolve().parent.parent / "memory"
        if alt.resolve() != self._memory.resolve():
            roots.append(alt)
        sibling = self._memory.parent / "app" / "memory"
        if sibling.is_dir() and sibling.resolve() not in {r.resolve() for r in roots}:
            roots.append(sibling)

        file_names = (
            "opportunities.jsonl",
            "quality_archive.jsonl",
            "opportunity_journal.jsonl",
        )
        for root in roots:
            for name in file_names:
                added += self.ingest_jsonl(root / name, source=f"bootstrap:{root.name}/{name}")
            added += self.ingest_jsonl(
                root / "lead_engine_v2" / "contact_history.jsonl",
                source=f"bootstrap:{root.name}/contact_history",
            )
            # One-off backups that still hold sent history
            for backup in root.glob("opportunities*.jsonl"):
                if backup.name in file_names:
                    continue
                added += self.ingest_jsonl(backup, source=f"bootstrap:{backup.name}")
            archive = root / "lead_engine_v1_archive"
            if archive.is_dir():
                for stamp_dir in archive.iterdir():
                    if not stamp_dir.is_dir():
                        continue
                    for name in (
                        "opportunities.jsonl",
                        "opportunities_snapshot.jsonl",
                        "contact_history.jsonl",
                        "quality_archive.jsonl",
                    ):
                        added += self.ingest_jsonl(
                            stamp_dir / name,
                            source=f"archive:{stamp_dir.name}/{name}",
                        )
        after = self._load()
        return {
            "ok": True,
            "emails_before": before_n,
            "emails_after": len(after.get("emails") or {}),
            "hosts_after": len(after.get("hosts") or {}),
            "rows_touched": added,
            "path": str(self._path),
        }

    def counts(self) -> dict[str, int]:
        data = self._load()
        return {
            "emails": len(data.get("emails") or {}),
            "hosts": len(data.get("hosts") or {}),
        }
