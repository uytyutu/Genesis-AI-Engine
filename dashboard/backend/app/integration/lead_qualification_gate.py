"""Mission 2 — обязательная квалификация лида перед КП/письмом."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_JUNK_EMAIL_SUFFIXES = ("example.com", "wixpress.com", "sentry.io", "cloudflare.com")

_SKIP_DOMAINS = frozenset(
    {
        "wikipedia.org",
        "python.org",
        "mozilla.org",
        "debian.org",
        "nginx.com",
        "cloudflare.com",
        "f5.com",
        "example.com",
        "google.com",
        "facebook.com",
        "github.com",
        "apache.org",
    }
)


def extract_emails_from_text(text: str) -> list[str]:
    found: list[str] = []
    for match in _EMAIL_RE.findall(text or ""):
        low = match.lower()
        if any(low.endswith(f"@{s}") or f"@{s}" in low for s in _JUNK_EMAIL_SUFFIXES):
            continue
        if match not in found:
            found.append(match)
    # Cap harvest; CCI ranks — do not treat order as selection.
    return found[:20]


def discover_contact_channels(
    *,
    contact: str,
    analysis: dict[str, Any] | None,
    website_url: str = "",
) -> dict[str, Any]:
    """Resolve commercial contact via CCI (never first-email-wins)."""
    from app.integration.cci import decision_to_dict, resolve_commercial_contact

    emails = extract_emails_from_text(contact or "")
    if analysis:
        emails.extend(analysis.get("emails_found") or [])
        for issue in analysis.get("issues") or []:
            emails.extend(extract_emails_from_text(str(issue)))
    unique: list[str] = []
    for e in emails:
        low = str(e).strip().lower()
        if low and low not in unique:
            unique.append(low)
    has_phone = bool(
        re.search(r"\+?\d[\d\s\-()]{7,}", contact or "")
        or (
            analysis
            and any(
                "whatsapp" in str(i).lower() or "tel:" in str(i).lower()
                for i in (analysis.get("issues") or [])
            )
        )
    )
    url = (
        website_url
        or str((analysis or {}).get("final_url") or "")
        or str((analysis or {}).get("url") or "")
    )
    decision = resolve_commercial_contact(emails=unique, website_url=url, html="")
    primary = decision.chosen or ""
    # Canon: auto commercial path needs CCI auto_send; phone-only still ok for non-email outreach.
    can_email = decision.decision == "auto_send" and bool(primary)
    return {
        "emails": unique[:8],
        "primary_email": primary,
        "has_phone_or_whatsapp": has_phone,
        "can_outreach": can_email or has_phone,
        "cci": decision_to_dict(decision),
    }


def build_audit_report_md(
    row: dict[str, Any],
    analysis: dict[str, Any] | None,
    *,
    service_label: str,
    price_eur: float,
    win_pct: int,
    price_label: str | None = None,
) -> str:
    company = str(row.get("company_name") or "Компания")
    url = str(row.get("website_url") or analysis.get("final_url") if analysis else "")
    issues = list((analysis or {}).get("issues") or [])[:8]
    title = str((analysis or {}).get("title") or "")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    price_txt = (price_label or "").strip() or f"{price_eur:.0f} €"

    lines = [
        f"# Аудит сайта — {company}",
        f"",
        f"**Дата:** {now} · **Virtus Core / Truth Engine**",
        f"**URL:** {url}",
        f"",
    ]
    if title:
        lines.append(f"**Заголовок страницы:** {title}")
        lines.append("")
    lines.append(f"## Найдено проблем: {len(issues)}")
    for i, issue in enumerate(issues, 1):
        lines.append(f"{i}. {issue}")
    lines.append("")
    lines.append("## Рекомендация")
    lines.append(f"- **Услуга:** {service_label}")
    lines.append(f"- **Ориентир цены:** {price_txt}")
    lines.append(f"- **Вероятность интереса (оценка):** {win_pct}%")
    lines.append("")
    lines.append(
        "_Отчёт сгенерирован автоматически по публичным данным сайта. "
        "Не является юридическим pentest._"
    )
    return "\n".join(lines)


def qualify_lead(
    row: dict[str, Any],
    analysis: dict[str, Any] | None,
    *,
    evaluation: dict[str, Any] | None = None,
    require_email: bool = False,
) -> dict[str, Any]:
    """Обязательные проверки перед подготовкой письма."""
    url = str(row.get("website_url") or "").strip()
    host = urlparse(url).netloc.lower().removeprefix("www.")
    steps: list[dict[str, Any]] = []

    def _step(step_id: str, title_ru: str, ok: bool | None, detail_ru: str) -> None:
        steps.append({"id": step_id, "title_ru": title_ru, "ok": ok, "detail_ru": detail_ru})

    # 1 — Discovery (уже в журнале)
    _step(
        "discovery",
        "Лид в Discovery",
        True,
        f"{row.get('company_name') or '—'} · score {row.get('score', '—')}",
    )

    # 2 — Оценка лида
    ev = evaluation or {}
    win = int(ev.get("win_probability_pct") or 0)
    _step(
        "lead_score",
        "Оценка лида",
        True if win >= 55 else False if win > 0 else None,
        f"Win {win}% · услуга {ev.get('service_label_ru') or '—'}",
    )

    # 3 — Сайт существует
    status = int((analysis or {}).get("status_code") or 0)
    site_ok = status > 0 and status < 500 and host not in _SKIP_DOMAINS
    if status == 403 and host in _SKIP_DOMAINS:
        site_ok = False
    _step(
        "site_exists",
        "Сайт доступен",
        site_ok,
        f"HTTP {status or '—'} · {host or 'нет URL'}",
    )

    # 4 — Компания активна (не пустышка)
    issue_count = int((analysis or {}).get("issue_count") or 0)
    html_issues = [str(i) for i in (analysis or {}).get("issues") or []]
    dead_signals = sum(
        1 for i in html_issues if any(x in i.lower() for x in ("baustelle", "coming soon", "veraltet"))
    )
    active = site_ok and issue_count >= 1 and dead_signals < 3
    _step(
        "company_active",
        "Компания / сайт активны",
        active,
        f"{issue_count} проблем · мёртвых сигналов {dead_signals}",
    )

    # 5 — Контакт (CCI — commercial mailbox, not first scrape hit)
    channels = discover_contact_channels(
        contact=str(row.get("contact") or ""),
        analysis=analysis,
        website_url=url,
    )
    email_ok = bool(channels["primary_email"])
    cci = channels.get("cci") if isinstance(channels.get("cci"), dict) else {}
    if require_email:
        contact_ok = email_ok
    else:
        contact_ok = channels["can_outreach"]
    detail_contact = channels["primary_email"] or (
        "телефон/WhatsApp" if channels["has_phone_or_whatsapp"] else "не найден"
    )
    if cci.get("decision") == "HOLD" and not channels["primary_email"]:
        detail_contact = f"CCI HOLD · conf {cci.get('contact_confidence', 0)}"
    _step(
        "email_found",
        "Контакт для outreach",
        contact_ok,
        detail_contact,
    )

    # 6 — Оффер подходит
    price = float(ev.get("sell_price_eur") or row.get("recommended_price_eur") or 0)
    legal = bool((ev.get("legal_gate") or {}).get("legal", True))
    offer_ok = legal and 50 <= price <= 1200 and win >= 50
    _step(
        "offer_fit",
        "Оффер подходит",
        offer_ok,
        f"{ev.get('service_label_ru') or '—'} · {price:.0f} €",
    )

    checks_ok = [s["ok"] for s in steps if s["ok"] is not None]
    passed = all(checks_ok) if checks_ok else False
    blockers = [s["title_ru"] for s in steps if s["ok"] is False]

    return {
        "passed": passed,
        "steps": steps,
        "blockers_ru": blockers,
        "channels": channels,
        "pipeline_label_ru": (
            "Spider → Discovery → Оценка → Сайт → Контакт → КП → Approve → Отправка"
            if passed
            else "Остановлено до Approve — не прошла квалификация"
        ),
        "product_ru": "Продаём аудит/отчёт (50–500 €), не разметку за 0,05 €",
    }
