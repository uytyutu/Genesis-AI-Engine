"""Global Exclusion List — never re-contact the same email/host after outreach."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)

_EXCLUDED_CRM = frozenset(
    {"contacted", "replied", "qualified", "won", "lost", "blacklist"}
)
_EXCLUDED_OUTREACH = frozenset({"sent", "approved", "rejected"})


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


def _row_excluded(row: dict[str, Any]) -> bool:
    status = str(row.get("status") or "").strip().lower()
    outreach = str(row.get("outreach_status") or "").strip().lower()
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    if status in _EXCLUDED_CRM:
        return True
    if outreach in _EXCLUDED_OUTREACH:
        return True
    if meta.get("blacklist") or meta.get("do_not_contact"):
        return True
    tags = meta.get("tags") if isinstance(meta.get("tags"), list) else []
    if any(str(t).lower() in ("blacklist", "dnc", "do_not_contact") for t in tags):
        return True
    return False


def build_exclusion_index(rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    emails: set[str] = set()
    hosts: set[str] = set()
    for row in rows:
        if not _row_excluded(row):
            continue
        email = normalize_email(str(row.get("contact") or ""))
        if email:
            emails.add(email)
        host = normalize_host(str(row.get("website_url") or ""))
        if host:
            hosts.add(host)
    return {"emails": emails, "hosts": hosts}


def is_excluded(
    *,
    email: str | None = None,
    website_url: str | None = None,
    index: dict[str, set[str]] | None = None,
    rows: list[dict[str, Any]] | None = None,
    exclude_id: str | None = None,
) -> tuple[bool, str]:
    """Return (excluded, reason)."""
    idx = index or build_exclusion_index(
        [r for r in (rows or []) if not exclude_id or str(r.get("id")) != exclude_id]
    )
    em = normalize_email(email)
    if em and em in idx.get("emails", set()):
        return True, "email_already_contacted"
    host = normalize_host(website_url)
    if host and host in idx.get("hosts", set()):
        return True, "host_already_contacted"
    return False, ""


class GlobalExclusionService:
    """Thin helper bound to OpportunityService-like store."""

    def __init__(self, opportunity: Any) -> None:
        self._opportunity = opportunity

    def _rows(self) -> list[dict[str, Any]]:
        if hasattr(self._opportunity, "_load_rows"):
            return list(self._opportunity._load_rows())
        if hasattr(self._opportunity, "list_opportunities"):
            return list(self._opportunity.list_opportunities(limit=2000))
        return []

    def index(self) -> dict[str, set[str]]:
        return build_exclusion_index(self._rows())

    def check(
        self,
        *,
        email: str | None = None,
        website_url: str | None = None,
        exclude_id: str | None = None,
    ) -> tuple[bool, str]:
        return is_excluded(
            email=email,
            website_url=website_url,
            rows=self._rows(),
            exclude_id=exclude_id,
        )
