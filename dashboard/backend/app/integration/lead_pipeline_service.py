"""Lead pipeline — single ingest adapter + gate funnel metrics.

New data sources should only write a thin adapter that calls ingest_lead().
Quality / risk / niche / outbox rules stay in existing services (no policy_engine rewrite).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_DEMO_HOSTS = frozenset(
    {
        "wikipedia.org",
        "python.org",
        "mozilla.org",
        "debian.org",
        "nginx.com",
        "cloudflare.com",
        "example.com",
        "f5.com",
        "github.com",
        "google.com",
        "facebook.com",
        "apache.org",
    }
)


def _host(url: str) -> str:
    host = (urlparse(url or "").hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def is_blocked_host(url: str) -> bool:
    host = _host(url)
    if not host:
        return False
    return any(host == d or host.endswith("." + d) for d in _DEMO_HOSTS)


def detect_niche_key(*, company: str = "", query: str = "", meta: dict | None = None) -> str:
    """Lightweight niche tag for templates — not a Niche Engine."""
    meta = meta or {}
    explicit = str(meta.get("niche") or meta.get("classified_niche") or "").casefold()
    blob = " ".join(
        [
            company,
            query,
            explicit,
            str(meta.get("types") or ""),
            str(meta.get("place_types") or ""),
        ]
    ).casefold()
    if any(
        k in blob
        for k in (
            "zahn",
            "dental",
            "stomat",
            "orthodont",
            "kieferorth",
        )
    ):
        return "zahnarzt"
    if any(
        k in blob
        for k in (
            "kfz",
            "auto",
            "werkstatt",
            "reparatur",
            "garage",
            "car repair",
            "autowerk",
        )
    ):
        return "kfz"
    if any(k in blob for k in ("dach", "dachdecker", "roofer", "dachsanierung")):
        return "dach"
    return "general"


def ingest_lead(
    opportunity_service: Any,
    payload: dict[str, Any],
    *,
    dedupe_by: str = "auto",
) -> dict[str, Any]:
    """Единая точка входа: любой источник → opportunity row.

    Adapter writes only source-specific fields; shared gates run later via
    prepare / auto_prepare / evaluate_opportunity.
    """
    source_id = str(payload.get("source_id") or "manual").strip() or "manual"
    company = str(payload.get("company_name") or "").strip()
    if not company:
        raise ValueError("company_required")

    website = str(payload.get("website_url") or "").strip()
    if website and is_blocked_host(website):
        return {
            "ok": False,
            "created": False,
            "duplicate": False,
            "blocked": True,
            "reason": "blocked_host",
            "row": None,
        }

    meta_in = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    niche = detect_niche_key(company=company, query=str(payload.get("query") or ""), meta=meta_in)
    meta = {
        **meta_in,
        "niche": meta_in.get("niche") or niche,
        "ingested_via": "ingest_lead",
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }

    place_id = str(meta.get("place_id") or "").strip()
    contact = str(payload.get("contact") or "").strip()

    existing = _find_duplicate(
        opportunity_service,
        website=website,
        place_id=place_id,
        contact=contact,
        company=company,
        mode=dedupe_by,
    )
    if existing:
        updates: dict[str, Any] = {
            "meta": {**(existing.get("meta") or {}), **meta, "ingest_duplicate": True},
        }
        if website and not existing.get("website_url"):
            updates["website_url"] = website
        if contact and not existing.get("contact"):
            updates["contact"] = contact
        if payload.get("fit_reason"):
            updates["fit_reason"] = payload["fit_reason"]
        row = opportunity_service.update(existing["id"], updates) or existing
        return {
            "ok": True,
            "created": False,
            "duplicate": True,
            "blocked": False,
            "reason": "duplicate",
            "row": row,
        }

    create_payload = {
        "source_id": source_id,
        "opportunity_type": payload.get("opportunity_type") or "lead",
        "company_name": company,
        "contact": contact,
        "website_url": website,
        "fit_reason": payload.get("fit_reason") or "",
        "notes": payload.get("notes") or "",
        "score": payload.get("score"),
        "potential_value_eur": payload.get("potential_value_eur") or 0,
        "meta": meta,
        "site_analysis": payload.get("site_analysis"),
        "proposed_message": payload.get("proposed_message") or "",
    }
    row = opportunity_service.create(create_payload)
    return {
        "ok": True,
        "created": True,
        "duplicate": False,
        "blocked": False,
        "reason": "created",
        "row": row,
    }


def _find_duplicate(
    opportunity_service: Any,
    *,
    website: str,
    place_id: str,
    contact: str,
    company: str,
    mode: str,
) -> dict[str, Any] | None:
    rows = opportunity_service.list_opportunities(limit=500)
    host = _host(website) if website else ""
    company_key = company.casefold().strip()
    contact_key = contact.casefold().strip()

    for row in rows:
        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        if place_id and str(meta.get("place_id") or "").strip() == place_id:
            return row
        if host and _host(str(row.get("website_url") or "")) == host:
            return row
        if mode != "strict" and contact_key and str(row.get("contact") or "").casefold().strip() == contact_key:
            return row
        if mode == "loose" and company_key and str(row.get("company_name") or "").casefold().strip() == company_key:
            return row
    return None


def gate_funnel_metrics(
    opportunity_service: Any,
    *,
    memory_dir: Path | None = None,
) -> dict[str, Any]:
    """Пульс конвейера Country Desk — без нового policy_engine."""
    mem = Path(memory_dir or getattr(opportunity_service, "memory_dir", None) or _DEFAULT_MEMORY)
    rows = opportunity_service.list_opportunities(limit=1000)

    found = len(rows)
    duplicates = 0
    quality_archive = 0
    manual_review = 0
    pending_approval = 0
    sent = 0
    replied = 0
    won = 0
    lost = 0
    blocked_hosts = 0

    for row in rows:
        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        if meta.get("ingest_duplicate"):
            duplicates += 1
        if meta.get("quality_archive"):
            quality_archive += 1
        status = str(row.get("status") or "")
        outreach = str(row.get("outreach_status") or "")
        if outreach == "manual_review":
            manual_review += 1
        if outreach == "pending_approval":
            pending_approval += 1
        if outreach in ("sent", "approved") or status == "contacted":
            sent += 1
        if status == "won":
            won += 1
        if status == "lost":
            lost += 1
        interactions = row.get("interactions") if isinstance(row.get("interactions"), list) else []
        if any(
            str((i or {}).get("event") or "").lower() in ("replied", "reply", "ответил", "answer")
            for i in interactions
            if isinstance(i, dict)
        ):
            replied += 1
        if is_blocked_host(str(row.get("website_url") or "")):
            blocked_hosts += 1

    archive_file = mem / "quality_archive.jsonl"
    archive_lines = 0
    if archive_file.is_file():
        archive_lines = sum(1 for ln in archive_file.read_text(encoding="utf-8").splitlines() if ln.strip())
    # Prefer live meta count; file is cumulative history
    quality_total = max(quality_archive, archive_lines) if archive_lines else quality_archive

    lost_file = mem / "lost_reasons.jsonl"
    lost_journal = 0
    if lost_file.is_file():
        lost_journal = sum(1 for ln in lost_file.read_text(encoding="utf-8").splitlines() if ln.strip())

    ready_review = manual_review + pending_approval
    # Approximate "scanned" as found + blocked sense: use found as base
    stages = [
        {"id": "found", "label_ru": "Найдено", "count": found},
        {"id": "duplicates", "label_ru": "Дубликаты", "count": duplicates},
        {"id": "quality_archive", "label_ru": "Архив качества", "count": quality_total},
        {"id": "manual_review", "label_ru": "Manual review", "count": manual_review},
        {"id": "approve", "label_ru": "Approve", "count": pending_approval},
        {"id": "sent", "label_ru": "Отправлено", "count": sent},
        {"id": "replied", "label_ru": "Ответили", "count": replied},
        {"id": "won", "label_ru": "Оплатили / won", "count": won},
        {"id": "lost", "label_ru": "Отказы (lost)", "count": max(lost, lost_journal)},
    ]

    # Drop-off hints for CEO pulse
    bottleneck = "—"
    if found and quality_total >= max(1, found // 3):
        bottleneck = "Quality Gate (много в архиве)"
    elif found and pending_approval == 0 and manual_review == 0 and sent == 0:
        bottleneck = "Нет черновиков — обновите поиск лидов"
    elif pending_approval > 0 and sent == 0:
        bottleneck = "Approve CEO (письма ждут)"
    elif sent > 0 and replied == 0 and won == 0:
        bottleneck = "Ответы клиентов (после отправки)"
    elif replied > 0 and won == 0:
        bottleneck = "Оплата / закрытие сделки"

    return {
        "ok": True,
        "title_ru": "Пульс гейтов · Country Desk",
        "hint_ru": (
            "Один конвейер для всех источников. Смотри, где теряются лиды — "
            "не строй новый engine ради файла."
        ),
        "bottleneck_ru": bottleneck,
        "stages": stages,
        "summary": {
            "found": found,
            "duplicates": duplicates,
            "quality_archive": quality_total,
            "manual_review": manual_review,
            "approve": pending_approval,
            "ready_review": ready_review,
            "sent": sent,
            "replied": replied,
            "won": won,
            "lost": max(lost, lost_journal),
            "blocked_hosts": blocked_hosts,
        },
        "pulse_ru": (
            f"Найдено: {found} → дубли: {duplicates} → архив качества: {quality_total} → "
            f"manual: {manual_review} → Approve: {pending_approval} → "
            f"отправлено: {sent} → ответили: {replied} → оплатили: {won}"
        ),
    }
