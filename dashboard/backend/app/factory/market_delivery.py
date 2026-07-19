"""Market-aware Path A delivery: status copy, ZIP README, legal pack selection.

Honest rule: never ship DE Impressum to a non-DE market. If no legal pack exists,
write LEGAL_NOTICE.txt instead of wrong-jurisdiction documents.

Delivery maturity (Path A support matrix):
  Level 1 — Production: currency + native UI + real legal pack (DACH, EN markets).
  Level 2 — Beta: currency + EN status UI + LEGAL_NOTICE (no fake local counsel).
  Level 3 — Beta: currency + localized status (uk/ru) + LEGAL_NOTICE (legal TBD).
"""

from __future__ import annotations

from typing import Any, Literal

# UI / receipt language for client-facing order status (not CEO console).
_MARKET_LANG: dict[str, str] = {
    "DE": "de",
    "AT": "de",
    "CH": "de",
    "US": "en",
    "GB": "en",
    "CA": "en",
    "AU": "en",
    "NZ": "en",
    "IE": "en",
    "FR": "en",
    "IT": "en",
    "ES": "en",
    "NL": "en",
    "BE": "en",
    "PT": "en",
    "PL": "en",
    "CZ": "en",
    "SK": "en",
    "RO": "en",
    "UA": "uk",
    "RU": "ru",
}

# Legal pack id by market. Only generate real templates when pack is known.
_MARKET_LEGAL: dict[str, str] = {
    "DE": "de_impressum",
    "AT": "de_impressum",
    "CH": "de_impressum",
    "US": "us_privacy",
    "CA": "us_privacy",
    "GB": "uk_privacy",
    "IE": "uk_privacy",
    "AU": "us_privacy",
    "NZ": "us_privacy",
    # Remaining EU / CIS — placeholder until local counsel templates exist
    "FR": "placeholder",
    "IT": "placeholder",
    "ES": "placeholder",
    "NL": "placeholder",
    "BE": "placeholder",
    "PT": "placeholder",
    "PL": "placeholder",
    "CZ": "placeholder",
    "SK": "placeholder",
    "RO": "placeholder",
    "UA": "placeholder",
    "RU": "placeholder",
}

# Markets covered by Path A delivery matrix (explicit support, not silent DE).
PATH_A_DELIVERY_MARKETS: tuple[str, ...] = tuple(
    sorted(set(_MARKET_LANG) | set(_MARKET_LEGAL))
)

DeliveryStatus = Literal["production", "beta"]
DeliveryLevel = Literal[1, 2, 3]

_STATUS_LABELS: dict[str, dict[str, str]] = {
    "de": {
        "awaiting_payment": "Wartet auf Zahlung",
        "pending_confirmation": "Wartet auf Bestätigung",
        "confirmed": "Bestätigt",
        "paid": "Bezahlt",
        "in_production": "In Arbeit",
        "ready": "Fertig",
        "delivered": "An den Kunden übergeben",
    },
    "en": {
        "awaiting_payment": "Awaiting payment",
        "pending_confirmation": "Awaiting confirmation",
        "confirmed": "Confirmed",
        "paid": "Paid",
        "in_production": "In production",
        "ready": "Ready",
        "delivered": "Delivered",
    },
    "uk": {
        "awaiting_payment": "Очікує оплату",
        "pending_confirmation": "Очікує підтвердження",
        "confirmed": "Підтверджено",
        "paid": "Оплачено",
        "in_production": "У виробництві",
        "ready": "Готово",
        "delivered": "Передано клієнту",
    },
    "ru": {
        "awaiting_payment": "Ожидает оплату",
        "pending_confirmation": "Ожидает подтверждения",
        "confirmed": "Подтверждено",
        "paid": "Оплачено",
        "in_production": "В работе",
        "ready": "Готово",
        "delivered": "Передано клиенту",
    },
}

_TIMELINE: dict[str, dict[str, str]] = {
    "de": {"payment": "Zahlung eingegangen", "handoff": "Vorbereitung der Übergabe"},
    "en": {"payment": "Payment received", "handoff": "Preparing delivery"},
    "uk": {"payment": "Оплату отримано", "handoff": "Підготовка передачі"},
    "ru": {"payment": "Оплата получена", "handoff": "Подготовка передачи"},
}

_NEXT_STEP: dict[str, dict[str, str]] = {
    "de": {
        "awaiting_payment": "Zahlung abschließen",
        "paid": "Übergabe der abgestimmten Version",
        "in_production": "Übergabe der abgestimmten Version",
        "ready": "Website-Archiv herunterladen",
        "delivered": "Projekt abgeschlossen",
    },
    "en": {
        "awaiting_payment": "Complete payment",
        "paid": "Delivery of the agreed version",
        "in_production": "Delivery of the agreed version",
        "ready": "Download your website archive",
        "delivered": "Project complete",
    },
    "uk": {
        "awaiting_payment": "Завершіть оплату",
        "paid": "Передача узгодженої версії",
        "in_production": "Передача узгодженої версії",
        "ready": "Завантажте архів сайту",
        "delivered": "Проєкт завершено",
    },
    "ru": {
        "awaiting_payment": "Завершите оплату",
        "paid": "Передача согласованной версии",
        "in_production": "Передача согласованной версии",
        "ready": "Скачайте архив сайта",
        "delivered": "Проект завершён",
    },
}

_CURRENT_STEP: dict[str, dict[str, str]] = {
    "de": {
        "awaiting_payment": "Wir warten auf die Zahlung zur Projektfixierung",
        "paid": "Wir bereiten die abgestimmte Version zur Übergabe vor",
        "in_production": "Wir bereiten die abgestimmte Version zur Übergabe vor",
        "ready": "Projekt fertig — Übergabe wird vorbereitet",
        "delivered": "Projekt übergeben — danke für Ihr Vertrauen!",
    },
    "en": {
        "awaiting_payment": "Waiting for payment to confirm the project",
        "paid": "Preparing the agreed version for delivery",
        "in_production": "Preparing the agreed version for delivery",
        "ready": "Project ready — preparing handoff",
        "delivered": "Project delivered — thank you for your trust!",
    },
    "uk": {
        "awaiting_payment": "Очікуємо оплату для фіксації проєкту",
        "paid": "Готуємо узгоджену версію до передачі",
        "in_production": "Готуємо узгоджену версію до передачі",
        "ready": "Проєкт готовий — готуємо передачу",
        "delivered": "Проєкт передано — дякуємо за довіру!",
    },
    "ru": {
        "awaiting_payment": "Ждём оплату для фиксации проекта",
        "paid": "Готовим согласованную версию к передаче",
        "in_production": "Готовим согласованную версию к передаче",
        "ready": "Проект готов — готовим передачу",
        "delivered": "Проект передан — спасибо за доверие!",
    },
}


def normalize_market(code: str | None) -> str:
    c = (code or "DE").strip().upper() or "DE"
    if c == "UK":
        return "GB"
    return c


def market_ui_lang(market_code: str | None) -> str:
    return _MARKET_LANG.get(normalize_market(market_code), "en")


def market_legal_pack(market_code: str | None) -> str:
    return _MARKET_LEGAL.get(normalize_market(market_code), "placeholder")


def market_delivery_support(market_code: str | None) -> dict[str, Any]:
    """Single-market Path A support row (currency / UI / legal / maturity)."""
    code = normalize_market(market_code)
    ui = market_ui_lang(code)
    pack = market_legal_pack(code)
    legal_ready = pack != "placeholder"
    # Level 3: localized status language without a real legal pack (UA/RU).
    if not legal_ready and ui in ("uk", "ru"):
        level: DeliveryLevel = 3
        status: DeliveryStatus = "beta"
    elif not legal_ready:
        level = 2
        status = "beta"
    else:
        level = 1
        status = "production"
    return {
        "market_code": code,
        "currency": True,
        "ui_lang": ui,
        "ui_label": ui.upper(),
        "legal_pack": pack,
        "legal_ready": legal_ready,
        "legal_label": "Ready" if legal_ready else "Placeholder",
        "level": level,
        "status": status,
        "status_label": "Production" if status == "production" else "Beta",
    }


def list_path_a_delivery_matrix() -> list[dict[str, Any]]:
    """CEO/support matrix: every Path A market with delivery maturity."""
    return [market_delivery_support(code) for code in PATH_A_DELIVERY_MARKETS]


def client_status_label(status: str, market_code: str | None) -> str:
    lang = market_ui_lang(market_code)
    return (_STATUS_LABELS.get(lang) or _STATUS_LABELS["en"]).get(
        status, (_STATUS_LABELS["en"]).get(status, status)
    )


def client_timeline(status: str, market_code: str | None) -> list[dict[str, Any]]:
    lang = market_ui_lang(market_code)
    labels = _TIMELINE.get(lang) or _TIMELINE["en"]
    paid = status in ("paid", "in_production", "ready", "delivered")
    handoff = status in ("in_production", "ready", "delivered")
    return [
        {"id": "payment", "label": labels["payment"], "done": paid},
        {"id": "handoff", "label": labels["handoff"], "done": handoff},
    ]


def client_next_step(status: str, market_code: str | None) -> str:
    lang = market_ui_lang(market_code)
    table = _NEXT_STEP.get(lang) or _NEXT_STEP["en"]
    if status in table:
        return table[status]
    if status in ("paid", "in_production"):
        return table["in_production"]
    return table.get("ready", "")


def client_current_step(status: str, market_code: str | None) -> str:
    lang = market_ui_lang(market_code)
    table = _CURRENT_STEP.get(lang) or _CURRENT_STEP["en"]
    if status in table:
        return table[status]
    if status in ("paid", "in_production"):
        return table["in_production"]
    return table.get("ready", table.get("awaiting_payment", ""))


_README_DE = """# Website veröffentlichen (Path A)

## Modell (Pilot)
Wir helfen bei der Wahl eines passenden Hosting-Anbieters. Unter den beliebten Optionen
in Deutschland sind Hetzner, IONOS, All-Inkl und Netcup. Der Vertrag für Domain und Hosting
wird direkt zwischen Ihnen und dem gewählten Anbieter geschlossen.
Virtus Core verkauft die Website und den Einrichtungs-Service — nicht Domain/Hosting als Reseller.

## Beispiele (DE — Vertrag/Zahlung bei Ihnen)
- Hetzner — https://www.hetzner.com/
- IONOS — https://www.ionos.de/
- All-Inkl — https://all-inkl.com/
- Netcup — https://www.netcup.de/

## Schritte
1. Archiv entpacken.
2. index.html, impressum.html und datenschutz.html im Browser prüfen.
3. Impressum und Datenschutz nur freigeben, wenn alle Angaben stimmen.
4. Dateien auf Ihr Hosting laden (FTP / Dateimanager).

Nicht im ZIP-Preis: Domain-Kauf, Hosting-Miete, laufende Anbieter-Gebühren.
Hinweis: Rechtsseiten sind Vorlagen — keine Rechtsberatung.

Erstellt von Factory · Virtus Core.
"""

_README_US = """# Publish your website (Path A)

## How it works
Virtus Core delivers a finished landing page (HTML). You keep ownership of the files.
Domain and hosting contracts are between you and your provider — we are not a reseller.

## Common hosting options (US / global)
- Cloudflare Pages — https://pages.cloudflare.com/
- Vercel — https://vercel.com/
- Netlify — https://www.netlify.com/
- GitHub Pages — https://pages.github.com/

## Steps
1. Unzip the archive.
2. Open index.html in your browser.
3. Review privacy.html and terms.html (templates — not legal advice). Replace placeholders before go-live.
4. Upload files to your host (drag-and-drop / FTP / CLI).

Not included in the package price: domain purchase, hosting fees, ongoing provider charges.

Built by Factory · Virtus Core.
"""

_README_UK = """# Publish your website (Path A — UK)

Virtus Core delivers finished HTML files. Domain and hosting stay on your contracts.

Suggested hosts: Cloudflare Pages, Vercel, Netlify, or your existing UK provider.

1. Unzip the archive.
2. Review privacy.html and terms.html before publishing (templates — not legal advice).
3. Upload to your host.

Built by Factory · Virtus Core.
"""

_README_PLACEHOLDER = """# Publish your website (Path A)

Virtus Core delivers finished HTML (index.html).

Legal documents for this market are not yet included in this ZIP.
Do not use German Impressum/Datenschutz templates for this market.
Add Privacy / Terms appropriate to your country before go-live (your counsel).

Hosting: upload index.html via your provider (Cloudflare Pages, Vercel, Netlify, or local host).

Built by Factory · Virtus Core.
"""

_README_UA = """# Публікація сайту (Path A)

Virtus Core передає готові HTML-файли. Домен і хостинг — ваш договір з провайдером.

Юридичні документи для цього ринку ще не включені в ZIP.
Не використовуйте німецький Impressum для України — додайте Privacy/Terms за порадою юриста.

Хостинг: Cloudflare Pages, Vercel, Netlify або ваш провайдер.

Factory · Virtus Core.
"""

_README_RU = """# Публикация сайта (Path A)

Virtus Core передаёт готовые HTML-файлы. Домен и хостинг — ваш договор с провайдером.

Юридические документы для этого рынка пока не включены в ZIP.
Не используйте немецкий Impressum — добавьте Privacy/Terms по совету юриста.

Хостинг: Cloudflare Pages, Vercel, Netlify или ваш провайдер.

Factory · Virtus Core.
"""


def deploy_readme(market_code: str | None) -> str:
    code = normalize_market(market_code)
    pack = market_legal_pack(code)
    if pack == "de_impressum":
        return _README_DE
    if pack == "us_privacy":
        return _README_US
    if pack == "uk_privacy":
        return _README_UK
    if code == "UA":
        return _README_UA
    if code == "RU":
        return _README_RU
    return _README_PLACEHOLDER


def legal_notice_placeholder(market_code: str | None) -> str:
    code = normalize_market(market_code)
    return (
        f"Legal documents for market {code} are not yet included.\n"
        "German Impressum / Datenschutz were intentionally NOT generated for this order.\n"
        "Add Privacy Policy and Terms appropriate to your jurisdiction before go-live.\n"
        "This notice is not legal advice.\n"
    )
