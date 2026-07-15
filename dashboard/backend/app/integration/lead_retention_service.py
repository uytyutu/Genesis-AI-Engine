"""DSGVO retention — purge stale lead phone numbers from opportunity journal."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{2,4}\)?[\s\-]?)?\d{3,4}[\s\-]?\d{3,4}(?:[\s\-]?\d{2,4})?"
)
_PHONE_IN_NOTES_RE = re.compile(
    r"(?i)(телефон|telefon|phone|whatsapp|mobil|handy)\s*:\s*[^\n]+"
)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _row_age_dt(row: dict[str, Any]) -> datetime | None:
    for key in ("updated_at", "found_at", "created_at"):
        dt = _parse_dt(str(row.get(key) or ""))
        if dt is not None:
            return dt
    return None


def strip_phone_from_text(text: str) -> tuple[str, bool]:
    """Remove phone-like tokens from free text; keep emails."""
    original = text or ""
    if not original.strip():
        return original, False
    cleaned = _PHONE_IN_NOTES_RE.sub(r"\1: [entfernt]", original)
    changed = cleaned != original
    for match in _PHONE_RE.finditer(cleaned):
        span = match.group(0)
        if "@" in span:
            continue
        digits = sum(ch.isdigit() for ch in span)
        if digits >= 7:
            cleaned = cleaned.replace(span, "[Telefon entfernt]", 1)
            changed = True
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned, changed


def purge_stale_lead_phones(
    memory_dir: Path | None = None,
    *,
    max_age_days: int = 90,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Drop phone numbers from opportunities older than max_age_days (DSGVO Speicherbegrenzung)."""
    root = memory_dir or _DEFAULT_MEMORY
    path = root / "opportunities.jsonl"
    if not path.is_file():
        return {
            "ok": True,
            "scanned": 0,
            "purged_rows": 0,
            "dry_run": dry_run,
            "message": "opportunities.jsonl not found",
        }

    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, int(max_age_days)))
    rows: list[dict[str, Any]] = []
    purged_ids: list[str] = []

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        age_dt = _row_age_dt(row)
        if age_dt is None or age_dt > cutoff:
            rows.append(row)
            continue

        changed = False
        contact, contact_changed = strip_phone_from_text(str(row.get("contact") or ""))
        if contact_changed:
            row["contact"] = contact
            changed = True

        notes, notes_changed = strip_phone_from_text(str(row.get("notes") or ""))
        if notes_changed:
            row["notes"] = notes
            changed = True

        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        for key in ("phone", "customer_phone"):
            if meta.get(key):
                meta.pop(key, None)
                changed = True
        if changed:
            meta["pii_phone_purged_at"] = datetime.now(timezone.utc).isoformat()
            row["meta"] = meta
            purged_ids.append(str(row.get("id") or ""))

        rows.append(row)

    if not dry_run and purged_ids:
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""),
            encoding="utf-8",
        )

    return {
        "ok": True,
        "scanned": len(rows),
        "purged_rows": len(purged_ids),
        "purged_ids": purged_ids[:20],
        "max_age_days": max_age_days,
        "dry_run": dry_run,
        "cutoff_iso": cutoff.isoformat(),
        "message": (
            f"{'Would purge' if dry_run else 'Purged'} phones in {len(purged_ids)} lead(s) "
            f"older than {max_age_days} days"
        ),
    }
