"""Market-aware Path A delivery: status copy, ZIP README, legal pack selection.

Honest rule: never ship DE Impressum to a non-DE market. If no legal pack exists,
write LEGAL_NOTICE.txt instead of wrong-jurisdiction documents.

Delivery maturity (Path A support matrix):
  Level 1 — Production: currency + native UI + real legal pack (DACH, EN markets).
  Level 2 — Beta: currency + EN status UI + LEGAL_NOTICE (no fake local counsel).
  Level 3 — Beta: currency + localized status (uk/ru) + LEGAL_NOTICE (legal TBD).
"""

from __future__ import annotations

from datetime import datetime, timezone
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
    "FR": "fr",
    "IT": "it",
    "ES": "es",
    "NL": "nl",
    "BE": "nl",
    "PT": "pt",
    "PL": "pl",
    "CZ": "cs",
    "SK": "sk",
    "RO": "ro",
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

# Live Factory progress after payment (Path A — minutes, not days).
_TIMELINE: dict[str, dict[str, str]] = {
    "de": {
        "payment": "Zahlung eingegangen",
        "analysis": "KI analysiert Ihr Unternehmen",
        "template": "Vorlage wird gewählt",
        "pages": "Seiten werden erzeugt",
        "seo": "SEO & Meta werden gesetzt",
        "packaging": "ZIP-Archiv wird gebaut",
        "ready": "Fertig — Download verfügbar",
    },
    "en": {
        "payment": "Payment received",
        "analysis": "AI analysing your business",
        "template": "Selecting template",
        "pages": "Generating pages",
        "seo": "Creating SEO & meta",
        "packaging": "Packaging ZIP",
        "ready": "Ready — download available",
    },
    "uk": {
        "payment": "Оплату отримано",
        "analysis": "ШІ аналізує ваш бізнес",
        "template": "Обираємо шаблон",
        "pages": "Генеруємо сторінки",
        "seo": "Готуємо SEO і meta",
        "packaging": "Збираємо ZIP-архів",
        "ready": "Готово — можна завантажити",
    },
    "ru": {
        "payment": "Оплата получена",
        "analysis": "ИИ анализирует ваш бизнес",
        "template": "Выбираем шаблон",
        "pages": "Генерируем страницы",
        "seo": "Готовим SEO и meta",
        "packaging": "Собираем ZIP-архив",
        "ready": "Готово — можно скачать",
    },
    "fr": {
        "payment": "Paiement reçu",
        "analysis": "IA analyse votre entreprise",
        "template": "Sélection du modèle",
        "pages": "Génération des pages",
        "seo": "SEO et meta",
        "packaging": "Création du ZIP",
        "ready": "Prêt — téléchargement disponible",
    },
    "es": {
        "payment": "Pago recibido",
        "analysis": "IA analiza su negocio",
        "template": "Selección de plantilla",
        "pages": "Generación de páginas",
        "seo": "SEO y meta",
        "packaging": "Empaquetando ZIP",
        "ready": "Listo — descarga disponible",
    },
    "it": {
        "payment": "Pagamento ricevuto",
        "analysis": "IA analizza la tua attività",
        "template": "Selezione del modello",
        "pages": "Generazione delle pagine",
        "seo": "SEO e meta",
        "packaging": "Creazione ZIP",
        "ready": "Pronto — download disponibile",
    },
    "nl": {
        "payment": "Betaling ontvangen",
        "analysis": "AI analyseert uw bedrijf",
        "template": "Sjabloon kiezen",
        "pages": "Pagina's genereren",
        "seo": "SEO & meta",
        "packaging": "ZIP maken",
        "ready": "Klaar — download beschikbaar",
    },
    "pt": {
        "payment": "Pagamento recebido",
        "analysis": "IA analisa o seu negócio",
        "template": "A escolher modelo",
        "pages": "A gerar páginas",
        "seo": "SEO e meta",
        "packaging": "A criar ZIP",
        "ready": "Pronto — download disponível",
    },
    "pl": {
        "payment": "Płatność otrzymana",
        "analysis": "AI analizuje firmę",
        "template": "Wybór szablonu",
        "pages": "Generowanie stron",
        "seo": "SEO i meta",
        "packaging": "Pakowanie ZIP",
        "ready": "Gotowe — można pobrać",
    },
    "cs": {
        "payment": "Platba přijata",
        "analysis": "AI analyzuje firmu",
        "template": "Výběr šablony",
        "pages": "Generování stránek",
        "seo": "SEO a meta",
        "packaging": "Sestavování ZIP",
        "ready": "Hotovo — ke stažení",
    },
}

_FACTORY_STEP_ORDER = (
    "payment",
    "analysis",
    "template",
    "pages",
    "seo",
    "packaging",
    "ready",
)

# Path A delivery promise — Factory builds in minutes, not business days.
PATH_A_ETA_MINUTES = 15

_NEXT_STEP: dict[str, dict[str, str]] = {
    "de": {
        "awaiting_payment": "Zahlung abschließen",
        "paid": "Factory erstellt Ihre Website",
        "in_production": "Factory erstellt Ihre Website",
        "ready": "Website-Archiv herunterladen",
        "delivered": "Projekt abgeschlossen",
    },
    "en": {
        "awaiting_payment": "Complete payment",
        "paid": "Factory is building your website",
        "in_production": "Factory is building your website",
        "ready": "Download your website archive",
        "delivered": "Project complete",
    },
    "uk": {
        "awaiting_payment": "Завершіть оплату",
        "paid": "Factory збирає ваш сайт",
        "in_production": "Factory збирає ваш сайт",
        "ready": "Завантажте архів сайту",
        "delivered": "Проєкт завершено",
    },
    "ru": {
        "awaiting_payment": "Завершите оплату",
        "paid": "Factory собирает ваш сайт",
        "in_production": "Factory собирает ваш сайт",
        "ready": "Скачайте архив сайта",
        "delivered": "Проект завершён",
    },
}

_CURRENT_STEP: dict[str, dict[str, str]] = {
    "de": {
        "awaiting_payment": "Wir warten auf die Zahlung zur Projektfixierung",
        "paid": "Automatische Erstellung läuft — meist ca. 15 Minuten",
        "in_production": "Automatische Erstellung läuft — meist ca. 15 Minuten",
        "ready": "Fertig — ZIP und Veröffentlichungs-Assistent bereit",
        "delivered": "Projekt übergeben — danke für Ihr Vertrauen!",
    },
    "en": {
        "awaiting_payment": "Waiting for payment to confirm the project",
        "paid": "Automatic build in progress — usually about 15 minutes",
        "in_production": "Automatic build in progress — usually about 15 minutes",
        "ready": "Ready — ZIP and go-live wizard available",
        "delivered": "Project delivered — thank you for your trust!",
    },
    "uk": {
        "awaiting_payment": "Очікуємо оплату для фіксації проєкту",
        "paid": "Автоматична збірка — зазвичай близько 15 хвилин",
        "in_production": "Автоматична збірка — зазвичай близько 15 хвилин",
        "ready": "Готово — ZIP і майстер публікації доступні",
        "delivered": "Проєкт передано — дякуємо за довіру!",
    },
    "ru": {
        "awaiting_payment": "Ждём оплату для фиксации проекта",
        "paid": "Автоматическая сборка — обычно около 15 минут",
        "in_production": "Автоматическая сборка — обычно около 15 минут",
        "ready": "Готово — ZIP и мастер публикации доступны",
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


def _ui_table(table: dict[str, dict[str, str]], market_code: str | None) -> dict[str, str]:
    lang = market_ui_lang(market_code)
    return table.get(lang) or table.get("en") or {}


def client_status_label(status: str, market_code: str | None) -> str:
    labels = _ui_table(_STATUS_LABELS, market_code)
    return labels.get(status, (_STATUS_LABELS["en"]).get(status, status))


def client_timeline(
    status: str,
    market_code: str | None,
    *,
    download_ready: bool = False,
    paid_at: str | None = None,
) -> list[dict[str, Any]]:
    """Live Factory progress for the order cabinet (trust UX after payment)."""
    labels = _ui_table(_TIMELINE, market_code) or _TIMELINE["en"]
    paid = status in ("paid", "in_production", "ready", "delivered")
    fully_ready = download_ready or status in ("ready", "delivered")

    done_count = 0
    if fully_ready:
        done_count = len(_FACTORY_STEP_ORDER)
    elif paid:
        # Progressive reveal while Factory runs (or until ZIP appears).
        elapsed = 0.0
        if paid_at:
            try:
                raw = paid_at.replace("Z", "+00:00")
                start = datetime.fromisoformat(raw)
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
                elapsed = max(0.0, (datetime.now(timezone.utc) - start).total_seconds())
            except ValueError:
                elapsed = 12.0
        # ~15s cadence across analysis→packaging; payment always first.
        thresholds = (0, 3, 8, 15, 25, 40, 55)
        done_count = 1
        for i, sec in enumerate(thresholds[1:], start=1):
            if elapsed >= sec:
                done_count = i + 1
            else:
                break
        done_count = min(done_count, len(_FACTORY_STEP_ORDER) - 1)

    out: list[dict[str, Any]] = []
    for i, step_id in enumerate(_FACTORY_STEP_ORDER):
        done = i < done_count
        active = paid and not fully_ready and i == done_count
        out.append(
            {
                "id": step_id,
                "label": labels.get(step_id, step_id),
                "done": done,
                "active": active,
            }
        )
    return out


def client_next_step(status: str, market_code: str | None) -> str:
    table = _ui_table(_NEXT_STEP, market_code) or _NEXT_STEP["en"]
    if status in table:
        return table[status]
    if status in ("paid", "in_production"):
        return table["in_production"]
    return table.get("ready", "")


def client_current_step(status: str, market_code: str | None) -> str:
    table = _ui_table(_CURRENT_STEP, market_code) or _CURRENT_STEP["en"]
    if status in table:
        return table[status]
    if status in ("paid", "in_production"):
        return table["in_production"]
    return table.get("ready", table.get("awaiting_payment", ""))


def client_post_pay_message(
    status: str,
    market_code: str | None,
    *,
    download_ready: bool = False,
) -> str:
    """Short trust message under the order cabinet timeline."""
    lang = market_ui_lang(market_code)
    ready = download_ready or status in ("ready", "delivered")
    copy = {
        "de": {
            "building": "Wir bereiten Ihre Website vor — meist in etwa 15 Minuten.",
            "ready": "Ihre Website-Dateien sind bereit. Laden Sie das ZIP herunter und folgen Sie dem Veröffentlichungs-Assistenten.",
            "awaiting": "Bitte schließen Sie die Zahlung ab — danach starten wir die automatische Erstellung.",
        },
        "en": {
            "building": "We’re building your website — usually ready in about 15 minutes.",
            "ready": "Your website files are ready. Download the ZIP and follow the go-live wizard.",
            "awaiting": "Please complete payment — then we start automatic generation.",
        },
        "uk": {
            "building": "Готуємо ваш сайт — зазвичай близько 15 хвилин.",
            "ready": "Файли сайту готові. Завантажте ZIP і пройдіть майстер публікації.",
            "awaiting": "Завершіть оплату — після цього стартує автоматична збірка.",
        },
        "ru": {
            "building": "Готовим ваш сайт — обычно около 15 минут.",
            "ready": "Файлы сайта готовы. Скачайте ZIP и пройдите мастер публикации.",
            "awaiting": "Завершите оплату — после этого стартует автоматическая сборка.",
        },
        "fr": {
            "building": "Nous préparons votre site — généralement en environ 15 minutes.",
            "ready": "Vos fichiers sont prêts. Téléchargez le ZIP et suivez l’assistant de mise en ligne.",
            "awaiting": "Veuillez finaliser le paiement — ensuite la génération démarre.",
        },
        "es": {
            "building": "Estamos preparando su sitio — normalmente en unos 15 minutos.",
            "ready": "Sus archivos están listos. Descargue el ZIP y siga el asistente de publicación.",
            "awaiting": "Complete el pago — después iniciaremos la generación automática.",
        },
        "it": {
            "building": "Stiamo preparando il sito — di solito in circa 15 minuti.",
            "ready": "I file sono pronti. Scarica lo ZIP e segui la procedura di pubblicazione.",
            "awaiting": "Completa il pagamento — poi avviamo la generazione automatica.",
        },
        "nl": {
            "building": "We bouwen uw website — meestal binnen ongeveer 15 minuten.",
            "ready": "Uw bestanden zijn klaar. Download de ZIP en volg de publicatie-assistent.",
            "awaiting": "Rond de betaling af — daarna start de automatische opbouw.",
        },
        "pt": {
            "building": "Estamos a preparar o seu site — normalmente em cerca de 15 minutos.",
            "ready": "Os ficheiros estão prontos. Descarregue o ZIP e siga o assistente de publicação.",
            "awaiting": "Conclua o pagamento — depois iniciamos a geração automática.",
        },
        "pl": {
            "building": "Budujemy stronę — zwykle w około 15 minut.",
            "ready": "Pliki są gotowe. Pobierz ZIP i przejdź kreator publikacji.",
            "awaiting": "Dokończ płatność — potem startuje automatyczna budowa.",
        },
        "cs": {
            "building": "Připravujeme váš web — obvykle do 15 minut.",
            "ready": "Soubory jsou připravené. Stáhněte ZIP a projděte průvodcem zveřejnění.",
            "awaiting": "Dokončete platbu — poté spustíme automatickou tvorbu.",
        },
    }
    pack = copy.get(lang) or copy["en"]
    if status == "awaiting_payment":
        return pack["awaiting"]
    if ready:
        return pack["ready"]
    return pack["building"]


def render_client_receipt_text(*, order: dict, status_path: str, paid: float) -> str:
    """Localized plain-text receipt for copy/email (market language)."""
    lang = market_ui_lang(order.get("market_code"))
    name = str(order.get("business_name") or "").strip() or "—"
    order_id = str(order.get("order_id") or "")
    package = str(order.get("package_name") or order.get("package_id") or "")
    amount = str(order.get("price_label") or f"{paid:.0f} {order.get('symbol') or '€'}".strip())
    paid_label = client_status_label("paid", order.get("market_code"))
    templates = {
        "de": (
            f"Virtus Core — Quittung\n\n"
            f"Bestellnummer: {order_id}\n"
            f"Kunde: {name}\n"
            f"Paket: {package}\n"
            f"Betrag: {amount}\n"
            f"Status: {paid_label}\n\n"
            f"Statusseite: {status_path}\n"
        ),
        "en": (
            f"Virtus Core — Receipt\n\n"
            f"Order: {order_id}\n"
            f"Customer: {name}\n"
            f"Package: {package}\n"
            f"Amount: {amount}\n"
            f"Status: {paid_label}\n\n"
            f"Order status: {status_path}\n"
        ),
        "uk": (
            f"Virtus Core — Чек\n\n"
            f"Замовлення: {order_id}\n"
            f"Клієнт: {name}\n"
            f"Пакет: {package}\n"
            f"Сума: {amount}\n"
            f"Статус: {paid_label}\n\n"
            f"Сторінка статусу: {status_path}\n"
        ),
        "ru": (
            f"Virtus Core — Чек\n\n"
            f"Заказ: {order_id}\n"
            f"Клиент: {name}\n"
            f"Пакет: {package}\n"
            f"Сумма: {amount}\n"
            f"Статус: {paid_label}\n\n"
            f"Страница статуса: {status_path}\n"
        ),
        "fr": (
            f"Virtus Core — Reçu\n\n"
            f"Commande: {order_id}\n"
            f"Client: {name}\n"
            f"Forfait: {package}\n"
            f"Montant: {amount}\n"
            f"Statut: {paid_label}\n\n"
            f"Suivi: {status_path}\n"
        ),
        "es": (
            f"Virtus Core — Recibo\n\n"
            f"Pedido: {order_id}\n"
            f"Cliente: {name}\n"
            f"Paquete: {package}\n"
            f"Importe: {amount}\n"
            f"Estado: {paid_label}\n\n"
            f"Estado del pedido: {status_path}\n"
        ),
        "it": (
            f"Virtus Core — Ricevuta\n\n"
            f"Ordine: {order_id}\n"
            f"Cliente: {name}\n"
            f"Pacchetto: {package}\n"
            f"Importo: {amount}\n"
            f"Stato: {paid_label}\n\n"
            f"Stato ordine: {status_path}\n"
        ),
        "nl": (
            f"Virtus Core — Bon\n\n"
            f"Bestelling: {order_id}\n"
            f"Klant: {name}\n"
            f"Pakket: {package}\n"
            f"Bedrag: {amount}\n"
            f"Status: {paid_label}\n\n"
            f"Statuspagina: {status_path}\n"
        ),
        "pt": (
            f"Virtus Core — Recibo\n\n"
            f"Encomenda: {order_id}\n"
            f"Cliente: {name}\n"
            f"Pacote: {package}\n"
            f"Valor: {amount}\n"
            f"Estado: {paid_label}\n\n"
            f"Estado da encomenda: {status_path}\n"
        ),
        "pl": (
            f"Virtus Core — Paragon\n\n"
            f"Zamówienie: {order_id}\n"
            f"Klient: {name}\n"
            f"Pakiet: {package}\n"
            f"Kwota: {amount}\n"
            f"Status: {paid_label}\n\n"
            f"Status zamówienia: {status_path}\n"
        ),
        "cs": (
            f"Virtus Core — Účtenka\n\n"
            f"Objednávka: {order_id}\n"
            f"Zákazník: {name}\n"
            f"Balíček: {package}\n"
            f"Částka: {amount}\n"
            f"Stav: {paid_label}\n\n"
            f"Stav objednávky: {status_path}\n"
        ),
    }
    return templates.get(lang) or templates["en"]


def delivery_ready_headline(market_code: str | None) -> str:
    lang = market_ui_lang(market_code)
    copy = {
        "de": "Ihr Website-Paket ist fertig",
        "en": "Your website package is ready",
        "uk": "Ваш пакет сайту готовий",
        "ru": "Ваш пакет сайта готов",
        "fr": "Votre pack site est prêt",
        "es": "Su paquete web está listo",
        "it": "Il tuo pacchetto sito è pronto",
        "nl": "Uw websitepakket is klaar",
        "pt": "O seu pacote de site está pronto",
        "pl": "Twój pakiet strony jest gotowy",
        "cs": "Váš balíček webu je připraven",
    }
    return copy.get(lang) or copy["en"]


def delivery_value_items(
    package_id: str | None,
    market_code: str | None,
) -> list[dict[str, str]]:
    """Honest list of what Path A ZIP contains for this package."""
    from app.factory.package_features import resolve_package_features

    lang = market_ui_lang(market_code)
    feat = resolve_package_features(package_id)
    labels = {
        "de": {
            "landing": "Landing Page",
            "seo": "SEO & Meta",
            "form": "Kontaktformular",
            "whatsapp": "WhatsApp-Button",
            "legal": "Rechtliche Seiten",
            "readme": "Veröffentlichungs-Anleitung",
            "zip": "ZIP-Archiv",
            "maps": "Google Maps",
            "faq": "FAQ",
            "logo": "Logo-Platz",
            "analytics": "Analytics-Platzhalter",
            "calculator": "Anfrage-Rechner",
            "premium": "Premium-Design",
        },
        "en": {
            "landing": "Landing Page",
            "seo": "SEO & Meta",
            "form": "Contact form",
            "whatsapp": "WhatsApp button",
            "legal": "Legal pages",
            "readme": "Publish guide (README)",
            "zip": "ZIP archive",
            "maps": "Google Maps",
            "faq": "FAQ",
            "logo": "Logo slot",
            "analytics": "Analytics placeholder",
            "calculator": "Quote calculator",
            "premium": "Premium design",
        },
        "uk": {
            "landing": "Landing Page",
            "seo": "SEO і Meta",
            "form": "Контактна форма",
            "whatsapp": "Кнопка WhatsApp",
            "legal": "Юридичні сторінки",
            "readme": "Інструкція з публікації",
            "zip": "ZIP-архів",
            "maps": "Google Maps",
            "faq": "FAQ",
            "logo": "Місце для логотипу",
            "analytics": "Analytics (заготовка)",
            "calculator": "Калькулятор запиту",
            "premium": "Premium-дизайн",
        },
        "ru": {
            "landing": "Landing Page",
            "seo": "SEO и Meta",
            "form": "Контактная форма",
            "whatsapp": "Кнопка WhatsApp",
            "legal": "Юридические страницы",
            "readme": "Инструкция по публикации",
            "zip": "ZIP-архив",
            "maps": "Google Maps",
            "faq": "FAQ",
            "logo": "Место под логотип",
            "analytics": "Analytics (заготовка)",
            "calculator": "Калькулятор заявки",
            "premium": "Premium-дизайн",
        },
    }
    L = labels.get(lang) or labels["en"]
    items: list[dict[str, str]] = [
        {"id": "landing", "label": L["landing"]},
        {"id": "seo", "label": L["seo"]},
        {"id": "form", "label": L["form"]},
    ]
    if feat.whatsapp:
        items.append({"id": "whatsapp", "label": L["whatsapp"]})
    if feat.maps:
        items.append({"id": "maps", "label": L["maps"]})
    if feat.faq:
        items.append({"id": "faq", "label": L["faq"]})
    if feat.logo_slot:
        items.append({"id": "logo", "label": L["logo"]})
    if feat.analytics:
        items.append({"id": "analytics", "label": L["analytics"]})
    if feat.calculator:
        items.append({"id": "calculator", "label": L["calculator"]})
    if feat.premium_design:
        items.append({"id": "premium", "label": L["premium"]})
    items.extend(
        [
            {"id": "legal", "label": L["legal"]},
            {"id": "readme", "label": L["readme"]},
            {"id": "zip", "label": L["zip"]},
        ]
    )
    return items


def publish_status_payload(
    *,
    market_code: str | None,
    downloaded: bool,
    online: bool,
    published_url: str | None,
    downloaded_at: str | None,
    online_at: str | None,
) -> dict[str, Any]:
    lang = market_ui_lang(market_code)
    labels = {
        "de": {
            "not_downloaded": "Noch nicht heruntergeladen",
            "downloaded": "Website heruntergeladen — noch nicht online",
            "online": "Website online",
        },
        "en": {
            "not_downloaded": "Not downloaded yet",
            "downloaded": "Website downloaded — not published yet",
            "online": "Website online",
        },
        "uk": {
            "not_downloaded": "Ще не завантажено",
            "downloaded": "Сайт завантажено — ще не опубліковано",
            "online": "Сайт online",
        },
        "ru": {
            "not_downloaded": "Ещё не скачан",
            "downloaded": "Сайт скачан — ещё не опубликован",
            "online": "Сайт online",
        },
    }
    L = labels.get(lang) or labels["en"]
    if online:
        state = "online"
    elif downloaded:
        state = "downloaded"
    else:
        state = "not_downloaded"
    return {
        "state": state,
        "label": L[state],
        "published_url": published_url,
        "downloaded_at": downloaded_at,
        "online_at": online_at,
    }


def next_product_offers(
    market_code: str | None,
    *,
    interest: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Soft LTV ladder after Path A site — interest only, not checkout yet."""
    lang = market_ui_lang(market_code)
    interest = interest or {}
    packs = {
        "de": {
            "ai_business_assistant": {
                "title": "AI Business Assistant",
                "subtitle": "Kein Chatbot — ein digitaler Mitarbeiter für Ihre Website.",
                "bullets": [
                    "Antwortet Besuchern 24/7",
                    "Nimmt Anfragen und Termine entgegen",
                    "Beantwortet häufige Fragen",
                    "Übergibt bei Bedarf an einen Menschen",
                ],
                "cta": "Interesse merken",
            },
            "whatsapp_business": {
                "title": "WhatsApp Business Anbindung",
                "subtitle": "Nachrichten von der Website direkt in WhatsApp.",
                "bullets": [
                    "Schneller Kontaktweg für Kunden",
                    "Weniger verlorene Anfragen",
                ],
                "cta": "Interesse merken",
            },
            "seo_growth": {
                "title": "SEO & Sichtbarkeit",
                "subtitle": "Nächster Schritt nach der fertigen Landing Page.",
                "bullets": [
                    "Lokale Auffindbarkeit",
                    "Seitenstruktur & Keywords",
                ],
                "cta": "Interesse merken",
            },
        },
        "en": {
            "ai_business_assistant": {
                "title": "AI Business Assistant",
                "subtitle": "Not a chatbot — a digital teammate for your site.",
                "bullets": [
                    "Answers visitors 24/7",
                    "Captures leads and bookings",
                    "Handles common questions",
                    "Hands off to a human when needed",
                ],
                "cta": "Register interest",
            },
            "whatsapp_business": {
                "title": "WhatsApp Business connection",
                "subtitle": "Site messages go straight to WhatsApp.",
                "bullets": [
                    "Faster customer contact",
                    "Fewer lost enquiries",
                ],
                "cta": "Register interest",
            },
            "seo_growth": {
                "title": "SEO & visibility",
                "subtitle": "Natural next step after your landing page.",
                "bullets": [
                    "Local discoverability",
                    "Structure & keywords",
                ],
                "cta": "Register interest",
            },
        },
        "uk": {
            "ai_business_assistant": {
                "title": "AI Business Assistant",
                "subtitle": "Не чат-бот — цифровий співробітник для сайту.",
                "bullets": [
                    "Відповідає відвідувачам 24/7",
                    "Збирає заявки та записи",
                    "Відповідає на часті питання",
                    "За потреби передає людині",
                ],
                "cta": "Залишити інтерес",
            },
            "whatsapp_business": {
                "title": "WhatsApp Business",
                "subtitle": "Повідомлення з сайту одразу у WhatsApp.",
                "bullets": ["Швидший контакт", "Менше втрачених заявок"],
                "cta": "Залишити інтерес",
            },
            "seo_growth": {
                "title": "SEO і видимість",
                "subtitle": "Наступний крок після готового лендингу.",
                "bullets": ["Локальна видимість", "Структура і ключові слова"],
                "cta": "Залишити інтерес",
            },
        },
        "ru": {
            "ai_business_assistant": {
                "title": "AI Business Assistant",
                "subtitle": "Не чат-бот — цифровой сотрудник для сайта.",
                "bullets": [
                    "Отвечает посетителям 24/7",
                    "Собирает заявки и записи",
                    "Отвечает на частые вопросы",
                    "При необходимости передаёт человеку",
                ],
                "cta": "Оставить интерес",
            },
            "whatsapp_business": {
                "title": "WhatsApp Business",
                "subtitle": "Сообщения с сайта сразу в WhatsApp.",
                "bullets": ["Быстрее контакт", "Меньше потерянных заявок"],
                "cta": "Оставить интерес",
            },
            "seo_growth": {
                "title": "SEO и видимость",
                "subtitle": "Следующий шаг после готового лендинга.",
                "bullets": ["Локальная видимость", "Структура и ключевые слова"],
                "cta": "Оставить интерес",
            },
        },
    }
    pack = packs.get(lang) or packs["en"]
    out: list[dict[str, Any]] = []
    for oid, meta in pack.items():
        out.append(
            {
                "id": oid,
                "title": meta["title"],
                "subtitle": meta["subtitle"],
                "bullets": list(meta["bullets"]),
                "cta": meta["cta"],
                "interest_logged": bool(interest.get(oid)),
            }
        )
    return out


_README_DE = """# Website veröffentlichen (Path A)

## Modell (Pilot)
Wir helfen bei der Wahl eines passenden Hosting-Anbieters. Unter den beliebten Optionen
in Deutschland sind Hetzner, IONOS, All-Inkl und Netcup. Der Vertrag für Domain und Hosting
wird direkt zwischen Ihnen und dem gewählten Anbieter geschlossen.
Im Lieferumfang: fertige Website und optional Hilfe bei der Einrichtung —
nicht Domain/Hosting als Reseller.

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

## Assisted Deployment (optional)
Auf der Bestellstatus-Seite können Sie „ZIP Only“ (selbst veröffentlichen) oder
„Assisted Deployment“ (Hilfe bei der Veröffentlichung) wählen.
Hosting-Passwörter werden nicht gespeichert — Sie bleiben Eigentümer von Domain,
Hosting, SSL und DNS. Details: Variante A (temporärer Zugang) oder B (Anleitung + Chat).

Nicht im ZIP-Preis: Domain-Kauf, Hosting-Miete, laufende Anbieter-Gebühren.
Hinweis: Rechtsseiten sind Vorlagen — keine Rechtsberatung.
"""

_README_US = """# Publish your website (Path A)

## How it works
You receive a finished landing page (HTML). You keep ownership of the files.
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

## Assisted Deployment (optional)
On your order status page you can choose “ZIP Only” (self-publish) or
“Assisted Deployment” (we help you go live). Hosting passwords are never stored —
you keep domain, hosting, SSL, and DNS. Prefer a temporary helper
account (Variant A) or stay logged in with guided steps (Variant B).

Not included in the package price: domain purchase, hosting fees, ongoing provider charges.
"""

_README_UK = """# Publish your website (Path A — UK)

You receive finished HTML files. Domain and hosting stay on your contracts.

Suggested hosts: Cloudflare Pages, Vercel, Netlify, or your existing UK provider.

1. Unzip the archive.
2. Review privacy.html and terms.html before publishing (templates — not legal advice).
3. Upload to your host.
"""

_README_PLACEHOLDER = """# Publish your website (Path A)

You receive finished HTML (index.html).

Legal documents for this market are not yet included as ready-made pages.
See LEGAL_NOTICE.txt in this ZIP for a market-specific checklist.
Do not use German Impressum/Datenschutz for this market.
Add the listed documents with your counsel before go-live.

Hosting: upload index.html via your provider (Cloudflare Pages, Vercel, Netlify, or local host).

On the order status page you may choose ZIP Only or Assisted Deployment
(hosting passwords are not stored).
"""

_README_UA = """# Публікація сайту (Path A)

Ви отримуєте готові HTML-файли. Домен і хостинг — ваш договір з провайдером.

Юридичні сторінки для цього ринку ще не включені як готові шаблони.
Див. LEGAL_NOTICE.txt у цьому ZIP — чеклист документів.
Не використовуйте німецький Impressum для України.

Хостинг: Cloudflare Pages, Vercel, Netlify або ваш провайдер.

На сторінці статусу замовлення можна обрати ZIP Only або Assisted Deployment
(паролі хостингу не зберігаються).
"""

_README_RU = """# Публикация сайта (Path A)

Вы получаете готовые HTML-файлы. Домен и хостинг — ваш договор с провайдером.

Юридические страницы для этого рынка пока не включены как готовые шаблоны.
См. LEGAL_NOTICE.txt в этом ZIP — чеклист документов.
Не используйте немецкий Impressum.

Хостинг: Cloudflare Pages, Vercel, Netlify или ваш провайдер.

На странице статуса заказа можно выбрать ZIP Only или Assisted Deployment
(пароли хостинга не хранятся).
"""


# Honest per-market document checklist (not legal advice; no fake counsel HTML).
_LEGAL_CHECKLISTS: dict[str, list[str]] = {
    "FR": [
        "Mentions légales (publisher / host / contact)",
        "Politique de confidentialité (RGPD)",
        "Cookie notice / consent if you use analytics or trackers",
        "CGU / conditions d'utilisation if you collect leads or sell online",
    ],
    "IT": [
        "Informativa privacy (GDPR)",
        "Cookie policy / banner if trackers are used",
        "Terms of use if you collect leads or sell online",
        "Company identification (ragione sociale, P.IVA where required)",
    ],
    "ES": [
        "Aviso legal / identificación del titular",
        "Política de privacidad (RGPD)",
        "Política de cookies if you use analytics or ads",
        "Condiciones de uso if you collect leads or sell online",
    ],
    "NL": [
        "Privacyverklaring (AVG/GDPR)",
        "Cookie notice if you use non-essential cookies",
        "Bedrijfsgegevens / contact on the site",
        "Algemene voorwaarden if you sell or take bookings online",
    ],
    "BE": [
        "Privacy policy (GDPR)",
        "Cookie notice if trackers are used",
        "Company identification / contact details",
        "Terms of use if you collect leads or sell online",
        "Language: match the language of your customers (FR/NL/DE as applicable)",
    ],
    "PT": [
        "Política de privacidade (RGPD)",
        "Aviso de cookies if trackers are used",
        "Identificação do responsável / contactos",
        "Termos de utilização if you collect leads or sell online",
    ],
    "PL": [
        "Polityka prywatności (RODO/GDPR)",
        "Informacja o plikach cookie if you use analytics",
        "Regulamin if you sell or take bookings online",
        "Dane firmowe / kontakt na stronie",
    ],
    "CZ": [
        "Zásady ochrany osobních údajů (GDPR)",
        "Cookie informace if trackers are used",
        "Obchodní podmínky if you sell or take bookings online",
        "Identifikace provozovatele / kontakt",
    ],
    "SK": [
        "Zásady ochrany osobných údajov (GDPR)",
        "Informácie o cookies if trackers are used",
        "Obchodné podmienky if you sell or take bookings online",
        "Identifikácia prevádzkovateľa / kontakt",
    ],
    "RO": [
        "Politică de confidențialitate (GDPR)",
        "Notă cookie if trackers are used",
        "Termeni și condiții if you sell or take bookings online",
        "Date de identificare / contact pe site",
    ],
    "UA": [
        "Політика конфіденційності",
        "Умови використання / оферта (якщо приймаєте заявки чи оплату онлайн)",
        "Повідомлення про cookies (якщо є аналітика)",
        "Реквізити / контакти власника сайту",
    ],
    "RU": [
        "Политика конфиденциальности",
        "Пользовательское соглашение / оферта (если принимаете заявки или оплату онлайн)",
        "Уведомление о cookies (если есть аналитика)",
        "Реквизиты / контакты владельца сайта",
    ],
}

_DEFAULT_LEGAL_CHECKLIST = [
    "Privacy Policy appropriate to your jurisdiction",
    "Terms of use / service if you collect leads or sell online",
    "Cookie / tracking notice if you use analytics or ads",
    "Clear business identity and contact details on the site",
]


def deploy_readme(market_code: str | None, package_id: str | None = None) -> str:
    code = normalize_market(market_code)
    pack = market_legal_pack(code)
    if pack == "de_impressum":
        body = _README_DE
    elif pack == "us_privacy":
        body = _README_US
    elif pack == "uk_privacy":
        body = _README_UK
    elif code == "UA":
        body = _README_UA
    elif code == "RU":
        body = _README_RU
    else:
        body = _README_PLACEHOLDER
    return _with_package_confirmation(body, package_id)


def _with_package_confirmation(body: str, package_id: str | None) -> str:
    """Prefix README with Layer A 'you paid for X' confirmation."""
    try:
        from app.integration.sales_order_service import (
            package_display_name,
            package_included_summary,
        )
    except Exception:
        return body
    name = package_display_name(package_id)
    included = package_included_summary(package_id)
    if not included:
        return body
    head = body.lstrip()[:120].lower()
    if body.lstrip().startswith("# Website veröffentlichen"):
        line = f"Sie haben das Paket {name} gewählt. Inklusive: {included}.\n\n"
    elif body.lstrip().startswith("# Publish"):
        line = f"You chose package {name}. Included: {included}.\n\n"
    elif "опублік" in head:
        line = f"Ви обрали пакет {name}. Включено: {included}.\n\n"
    elif "опублик" in head:
        line = f"Вы выбрали пакет {name}. Включено: {included}.\n\n"
    else:
        line = f"Package: {name}. Included: {included}.\n\n"
    return line + body


def market_legal_checklist(market_code: str | None) -> list[str]:
    code = normalize_market(market_code)
    return list(_LEGAL_CHECKLISTS.get(code) or _DEFAULT_LEGAL_CHECKLIST)


def legal_notice_placeholder(market_code: str | None) -> str:
    code = normalize_market(market_code)
    items = market_legal_checklist(code)
    lines = [
        f"LEGAL NOTICE — market {code}",
        "",
        "Path A delivery for this market does NOT include ready-made legal HTML pages.",
        "German Impressum / Datenschutz were intentionally NOT generated for this order.",
        "This file is a checklist only — not legal advice and not a substitute for counsel.",
        "",
        "Before go-live, add (with your lawyer / local requirements):",
    ]
    for i, item in enumerate(items, start=1):
        lines.append(f"  {i}. {item}")
    lines.extend(
        [
            "",
            "Until those pages exist, do not present this site as fully compliant for publishing.",
            "Keep ownership of your domain/hosting contracts with your provider.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"
