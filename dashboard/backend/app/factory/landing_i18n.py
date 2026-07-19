"""Factory landing chrome + niche copy by market UI language (de/en/uk/ru)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.factory.analyzer import AnalysisResult
from app.factory.market_delivery import market_legal_pack, market_ui_lang, normalize_market

# ISO country name fragment for maps query (not UI).
_MAPS_COUNTRY: dict[str, str] = {
    "DE": "Germany",
    "AT": "Austria",
    "CH": "Switzerland",
    "US": "USA",
    "GB": "United Kingdom",
    "CA": "Canada",
    "AU": "Australia",
    "NZ": "New Zealand",
    "IE": "Ireland",
    "FR": "France",
    "IT": "Italy",
    "ES": "Spain",
    "NL": "Netherlands",
    "BE": "Belgium",
    "PT": "Portugal",
    "PL": "Poland",
    "CZ": "Czechia",
    "SK": "Slovakia",
    "RO": "Romania",
    "UA": "Ukraine",
    "RU": "Russia",
}

_UI: dict[str, dict[str, str]] = {
    "de": {
        "services": "Leistungen",
        "why": "Warum {business}",
        "about": "Über uns",
        "contact": "Kontakt",
        "contact_muted": "Schreiben oder rufen Sie an — wir melden uns schnellstmöglich.",
        "phone": "Telefon",
        "email": "E-Mail",
        "hours": "Öffnungszeiten",
        "whatsapp": "WhatsApp",
        "whatsapp_send": "Nachricht senden",
        "reviews": "Kundenstimmen",
        "reviews_muted": "Beispieltexte — bitte durch echte Kundenstimmen ersetzen.",
        "maps": "Standort",
        "maps_muted": "So finden Sie uns — Karte anhand Ihrer Firmendaten.",
        "maps_iframe_title": "Karte",
        "calculator": "Kostenrechner",
        "calculator_muted": "Unverbindliche Schätzung — Details klären wir im Gespräch.",
        "calc_service": "Leistung",
        "calc_qty": "Anzahl",
        "calc_sum": "Summe",
        "calc_from": "ab",
        "calc_opt0": "Basis",
        "calc_opt1": "Standard",
        "calc_opt2": "Premium",
        "form_name": "Name",
        "form_name_ph": "Ihr Name",
        "form_phone": "Telefon",
        "form_phone_ph": "+49 …",
        "form_message": "Nachricht",
        "form_message_ph": "Kurz Ihr Anliegen",
        "form_submit": "Anfrage senden",
        "form_subject": "Anfrage Website",
        "legal_a": "Impressum",
        "legal_b": "Datenschutz",
        "legal_a_href": "impressum.html",
        "legal_b_href": "datenschutz.html",
        "t1": "«Professionell und zuverlässig — klare Empfehlung.»",
        "t1_cite": "— Anna K.",
        "t2": "«Transparente Preise und gutes Ergebnis.»",
        "t2_cite": "— Michael W.",
        "t3": "«Schnelle Terminvergabe und freundlicher Service.»",
        "t3_cite": "— Familie S.",
        "analytics_comment": "Google Analytics: Measurement-ID nach Go-live ersetzen (G-XXXXXXXXXX)",
    },
    "en": {
        "services": "Services",
        "why": "Why {business}",
        "about": "About us",
        "contact": "Contact",
        "contact_muted": "Message or call us — we will get back to you as soon as possible.",
        "phone": "Phone",
        "email": "Email",
        "hours": "Opening hours",
        "whatsapp": "WhatsApp",
        "whatsapp_send": "Send message",
        "reviews": "Reviews",
        "reviews_muted": "Sample quotes — please replace with real customer reviews.",
        "maps": "Location",
        "maps_muted": "Find us — map based on your business details.",
        "maps_iframe_title": "Map",
        "calculator": "Cost estimator",
        "calculator_muted": "Non-binding estimate — we confirm details in a call.",
        "calc_service": "Service",
        "calc_qty": "Quantity",
        "calc_sum": "Total",
        "calc_from": "from",
        "calc_opt0": "Basic",
        "calc_opt1": "Standard",
        "calc_opt2": "Premium",
        "form_name": "Name",
        "form_name_ph": "Your name",
        "form_phone": "Phone",
        "form_phone_ph": "+1 …",
        "form_message": "Message",
        "form_message_ph": "Briefly describe your request",
        "form_submit": "Send request",
        "form_subject": "Website enquiry",
        "legal_a": "Privacy",
        "legal_b": "Terms",
        "legal_a_href": "privacy.html",
        "legal_b_href": "terms.html",
        "t1": "«Professional and reliable — clear recommendation.»",
        "t1_cite": "— Anna K.",
        "t2": "«Transparent pricing and a solid result.»",
        "t2_cite": "— Michael W.",
        "t3": "«Fast appointment and friendly service.»",
        "t3_cite": "— The S. family",
        "analytics_comment": "Google Analytics: replace Measurement ID after go-live (G-XXXXXXXXXX)",
    },
    "uk": {
        "services": "Послуги",
        "why": "Чому {business}",
        "about": "Про нас",
        "contact": "Контакти",
        "contact_muted": "Напишіть або зателефонуйте — відповімо якнайшвидше.",
        "phone": "Телефон",
        "email": "Email",
        "hours": "Години роботи",
        "whatsapp": "WhatsApp",
        "whatsapp_send": "Написати",
        "reviews": "Відгуки",
        "reviews_muted": "Приклади текстів — замініть на реальні відгуки клієнтів.",
        "maps": "Розташування",
        "maps_muted": "Як нас знайти — карта за вашими даними.",
        "maps_iframe_title": "Карта",
        "calculator": "Калькулятор вартості",
        "calculator_muted": "Орієнтовна оцінка — деталі уточнимо в розмові.",
        "calc_service": "Послуга",
        "calc_qty": "Кількість",
        "calc_sum": "Сума",
        "calc_from": "від",
        "calc_opt0": "Базовий",
        "calc_opt1": "Стандарт",
        "calc_opt2": "Преміум",
        "form_name": "Ім’я",
        "form_name_ph": "Ваше ім’я",
        "form_phone": "Телефон",
        "form_phone_ph": "+380 …",
        "form_message": "Повідомлення",
        "form_message_ph": "Коротко опишіть запит",
        "form_submit": "Надіслати",
        "form_subject": "Запит з сайту",
        "legal_a": "Правова інформація",
        "legal_b": "Конфіденційність",
        "legal_a_href": "LEGAL_NOTICE.txt",
        "legal_b_href": "LEGAL_NOTICE.txt",
        "t1": "«Професійно і надійно — рекомендуємо.»",
        "t1_cite": "— Анна К.",
        "t2": "«Прозорі ціни і хороший результат.»",
        "t2_cite": "— Михайло В.",
        "t3": "«Швидкий запис і приємний сервіс.»",
        "t3_cite": "— родина С.",
        "analytics_comment": "Google Analytics: замініть Measurement ID після запуску (G-XXXXXXXXXX)",
    },
    "ru": {
        "services": "Услуги",
        "why": "Почему {business}",
        "about": "О нас",
        "contact": "Контакты",
        "contact_muted": "Напишите или позвоните — ответим как можно скорее.",
        "phone": "Телефон",
        "email": "Email",
        "hours": "Часы работы",
        "whatsapp": "WhatsApp",
        "whatsapp_send": "Написать",
        "reviews": "Отзывы",
        "reviews_muted": "Примеры текстов — замените на реальные отзывы клиентов.",
        "maps": "Адрес",
        "maps_muted": "Как нас найти — карта по данным компании.",
        "maps_iframe_title": "Карта",
        "calculator": "Калькулятор стоимости",
        "calculator_muted": "Ориентировочная оценка — детали уточним в разговоре.",
        "calc_service": "Услуга",
        "calc_qty": "Количество",
        "calc_sum": "Сумма",
        "calc_from": "от",
        "calc_opt0": "Базовый",
        "calc_opt1": "Стандарт",
        "calc_opt2": "Премиум",
        "form_name": "Имя",
        "form_name_ph": "Ваше имя",
        "form_phone": "Телефон",
        "form_phone_ph": "+7 …",
        "form_message": "Сообщение",
        "form_message_ph": "Кратко опишите запрос",
        "form_submit": "Отправить",
        "form_subject": "Запрос с сайта",
        "legal_a": "Правовая информация",
        "legal_b": "Конфиденциальность",
        "legal_a_href": "LEGAL_NOTICE.txt",
        "legal_b_href": "LEGAL_NOTICE.txt",
        "t1": "«Профессионально и надёжно — рекомендуем.»",
        "t1_cite": "— Анна К.",
        "t2": "«Прозрачные цены и хороший результат.»",
        "t2_cite": "— Михаил В.",
        "t3": "«Быстрая запись и приятный сервис.»",
        "t3_cite": "— семья С.",
        "analytics_comment": "Google Analytics: замените Measurement ID после запуска (G-XXXXXXXXXX)",
    },
}

# Niche body copy for non-DE markets (analyzer stays DE for lang=de).
_NICHE: dict[str, dict[str, dict[str, Any]]] = {
    "dental": {
        "en": {
            "headline": "{name} — modern dental care",
            "subtitle": "Clear treatment options, transparent pricing, easy appointment booking.",
            "services": ["Check-up & hygiene", "Fillings & restorations", "Implants & prosthetics", "Emergency care"],
            "descriptions": [
                "Preventive visits and cleaning",
                "Durable restorations",
                "Planned implant workflows",
                "Same-day advice when possible",
            ],
            "benefits": ["Transparent estimates", "Friendly team", "Modern equipment", "Central location"],
            "trust": ["Licensed practice", "Clear pricing", "Patient-first"],
            "about": "{name} focuses on careful diagnostics and understandable treatment plans.",
            "cta": "Book appointment",
            "hours": "Mon–Fri 9:00–18:00",
        },
        "uk": {
            "headline": "{name} — сучасна стоматологія",
            "subtitle": "Зрозумілі послуги, прозорі ціни, зручний запис.",
            "services": ["Огляд і гігієна", "Пломби та реставрації", "Імплантація", "Невідкладна допомога"],
            "descriptions": ["Профілактика", "Якісні реставрації", "Плановий імплант-workflow", "Швидка консультація"],
            "benefits": ["Прозорі оцінки", "Уважна команда", "Сучасне обладнання", "Зручне розташування"],
            "trust": ["Ліцензована практика", "Зрозумілі ціни", "Пацієнт у центрі"],
            "about": "{name} робить акцент на діагностиці та зрозумілих планах лікування.",
            "cta": "Записатися",
            "hours": "Пн–Пт 9:00–18:00",
        },
        "ru": {
            "headline": "{name} — современная стоматология",
            "subtitle": "Понятные услуги, прозрачные цены, удобная запись.",
            "services": ["Осмотр и гигиена", "Пломбы и реставрации", "Имплантация", "Неотложная помощь"],
            "descriptions": ["Профилактика", "Надёжные реставрации", "Плановый имплант-workflow", "Быстрая консультация"],
            "benefits": ["Прозрачные оценки", "Внимательная команда", "Современное оборудование", "Удобное расположение"],
            "trust": ["Лицензированная практика", "Понятные цены", "Пациент в центре"],
            "about": "{name} делает акцент на диагностике и понятных планах лечения.",
            "cta": "Записаться",
            "hours": "Пн–Пт 9:00–18:00",
        },
    },
    "auto": {
        "en": {
            "headline": "{name} — workshop you can trust",
            "subtitle": "Diagnostics, maintenance and repairs with clear estimates.",
            "services": ["Inspection", "Oil & filters", "Brakes", "Tyres"],
            "descriptions": ["Full check", "Scheduled service", "Safety-critical work", "Seasonal change"],
            "benefits": ["Honest quotes", "Qualified mechanics", "Parts transparency", "Fast turnaround"],
            "trust": ["Workshop guarantee", "Clear pricing", "Local service"],
            "about": "{name} keeps vehicles safe and road-ready with transparent communication.",
            "cta": "Book diagnostics",
            "hours": "Mon–Fri 8:00–17:00",
        },
        "uk": {
            "headline": "{name} — автосервіс, якому довіряють",
            "subtitle": "Діагностика, ТО і ремонт з прозорою оцінкою.",
            "services": ["Огляд", "Олива та фільтри", "Гальма", "Шини"],
            "descriptions": ["Повна перевірка", "Планове ТО", "Безпека", "Сезонна заміна"],
            "benefits": ["Чесні оцінки", "Кваліфіковані майстри", "Прозорі запчастини", "Швидкі строки"],
            "trust": ["Гарантія робіт", "Зрозумілі ціни", "Локальний сервіс"],
            "about": "{name} тримає авто в безпеці з прозорою комунікацією.",
            "cta": "Записати на діагностику",
            "hours": "Пн–Пт 8:00–17:00",
        },
        "ru": {
            "headline": "{name} — сервис, которому доверяют",
            "subtitle": "Диагностика, ТО и ремонт с понятной сметой.",
            "services": ["Осмотр", "Масло и фильтры", "Тормоза", "Шины"],
            "descriptions": ["Полная проверка", "Плановое ТО", "Безопасность", "Сезонная замена"],
            "benefits": ["Честные оценки", "Квалифицированные мастера", "Прозрачные запчасти", "Быстрые сроки"],
            "trust": ["Гарантия работ", "Понятные цены", "Локальный сервис"],
            "about": "{name} держит авто в безопасности с прозрачной коммуникацией.",
            "cta": "Записаться на диагностику",
            "hours": "Пн–Пт 8:00–17:00",
        },
    },
    "energy": {
        "en": {
            "headline": "{name} — solar & energy solutions",
            "subtitle": "Planning, installation support and clear next steps for your property.",
            "services": ["Site assessment", "System design", "Installation support", "Monitoring advice"],
            "descriptions": ["On-site review", "Sized to your roof", "Coordinated install", "Aftercare tips"],
            "benefits": ["Clear scope", "Local know-how", "Honest timeline", "Documented offer"],
            "trust": ["Qualified partners", "Transparent quote", "Local projects"],
            "about": "{name} helps households and businesses move to cleaner energy step by step.",
            "cta": "Request assessment",
            "hours": "Mon–Fri 9:00–17:00",
        },
        "uk": {
            "headline": "{name} — сонячна енергетика",
            "subtitle": "Оцінка, проєктування та зрозумілі кроки для вашого об’єкта.",
            "services": ["Огляд об’єкта", "Проєктування", "Супровід монтажу", "Моніторинг"],
            "descriptions": ["Виїзд", "Під ваш дах", "Координація", "Поради після запуску"],
            "benefits": ["Зрозумілий обсяг", "Локальний досвід", "Чесні строки", "Документований офер"],
            "trust": ["Кваліфіковані партнери", "Прозора ціна", "Локальні проєкти"],
            "about": "{name} допомагає переходити на чистішу енергію крок за кроком.",
            "cta": "Замовити оцінку",
            "hours": "Пн–Пт 9:00–17:00",
        },
        "ru": {
            "headline": "{name} — солнечная энергетика",
            "subtitle": "Оценка, проектирование и понятные шаги для вашего объекта.",
            "services": ["Осмотр объекта", "Проектирование", "Сопровождение монтажа", "Мониторинг"],
            "descriptions": ["Выезд", "Под вашу крышу", "Координация", "Советы после запуска"],
            "benefits": ["Понятный объём", "Локальный опыт", "Честные сроки", "Документированный оффер"],
            "trust": ["Квалифицированные партнёры", "Прозрачная цена", "Локальные проекты"],
            "about": "{name} помогает переходить на более чистую энергию шаг за шагом.",
            "cta": "Заказать оценку",
            "hours": "Пн–Пт 9:00–17:00",
        },
    },
    "generic": {
        "en": {
            "headline": "{name} — local service you can reach",
            "subtitle": "Clear offer, fast contact, professional delivery.",
            "services": ["Consultation", "Core service", "Follow-up", "Support"],
            "descriptions": ["Understand your need", "Deliver the job", "Check results", "Stay in touch"],
            "benefits": ["Local & reachable", "Clear pricing", "Reliable communication", "Quality focus"],
            "trust": ["Local business", "Transparent offer", "Customer care"],
            "about": "{name} helps local customers with a straightforward service offer.",
            "cta": "Contact us",
            "hours": "Mon–Fri 9:00–18:00",
        },
        "uk": {
            "headline": "{name} — локальний сервіс поруч",
            "subtitle": "Зрозуміла пропозиція, швидкий контакт, якісна робота.",
            "services": ["Консультація", "Основна послуга", "Супровід", "Підтримка"],
            "descriptions": ["З’ясуємо потребу", "Виконаємо роботу", "Перевіримо результат", "На зв’язку"],
            "benefits": ["Поруч", "Зрозумілі ціни", "Надійна комунікація", "Якість"],
            "trust": ["Локальний бізнес", "Прозора пропозиція", "Турбота про клієнта"],
            "about": "{name} допомагає місцевим клієнтам із зрозумілою пропозицією послуг.",
            "cta": "Зв’язатися",
            "hours": "Пн–Пт 9:00–18:00",
        },
        "ru": {
            "headline": "{name} — локальный сервис рядом",
            "subtitle": "Понятное предложение, быстрый контакт, качественная работа.",
            "services": ["Консультация", "Основная услуга", "Сопровождение", "Поддержка"],
            "descriptions": ["Выясним задачу", "Сделаем работу", "Проверим результат", "На связи"],
            "benefits": ["Рядом", "Понятные цены", "Надёжная коммуникация", "Качество"],
            "trust": ["Локальный бизнес", "Прозрачное предложение", "Забота о клиенте"],
            "about": "{name} помогает местным клиентам с понятным предложением услуг.",
            "cta": "Связаться",
            "hours": "Пн–Пт 9:00–18:00",
        },
    },
}

# Map other niches → generic pack (content) until dedicated packs exist.
_NICHE_ALIAS = {
    "law": "generic",
    "beauty": "generic",
    "green": "generic",
    "computer": "generic",
    "appliance": "generic",
    "handwerk": "generic",
}


def landing_lang_for_market(market_code: str | None) -> str:
    lang = market_ui_lang(market_code)
    return lang if lang in _UI else "en"


def ui_strings(lang: str) -> dict[str, str]:
    return dict(_UI.get(lang) or _UI["en"])


def apply_legal_footer_hrefs(ui: dict[str, str], market_code: str | None) -> dict[str, str]:
    """Adjust footer labels/hrefs to match shipped legal pack."""
    out = dict(ui)
    pack = market_legal_pack(market_code)
    if pack == "de_impressum":
        out["legal_a"] = _UI["de"]["legal_a"]
        out["legal_b"] = _UI["de"]["legal_b"]
        out["legal_a_href"] = "impressum.html"
        out["legal_b_href"] = "datenschutz.html"
    elif pack in ("us_privacy", "uk_privacy"):
        out["legal_a"] = "Privacy"
        out["legal_b"] = "Terms"
        out["legal_a_href"] = "privacy.html"
        out["legal_b_href"] = "terms.html"
    else:
        out["legal_a"] = out.get("legal_a") or "Legal"
        out["legal_b"] = out.get("legal_b") or "Privacy"
        out["legal_a_href"] = "LEGAL_NOTICE.txt"
        out["legal_b_href"] = "LEGAL_NOTICE.txt"
    return out


def maps_country_label(market_code: str | None) -> str:
    code = normalize_market(market_code)
    return _MAPS_COUNTRY.get(code, "Germany")


def localize_analysis(analysis: AnalysisResult, lang: str) -> AnalysisResult:
    """For de keep analyzer copy; for en/uk/ru overlay niche packs."""
    if lang == "de":
        return analysis
    pack_key = _NICHE_ALIAS.get(analysis.niche, analysis.niche)
    if pack_key not in _NICHE:
        pack_key = "generic"
    pack = (_NICHE.get(pack_key) or {}).get(lang) or (_NICHE["generic"].get(lang) or {})
    if not pack:
        return analysis
    name = analysis.business_name
    services = list(pack.get("services") or analysis.services)
    descriptions = list(pack.get("descriptions") or analysis.service_descriptions)
    if len(descriptions) < len(services):
        descriptions = descriptions + [""] * (len(services) - len(descriptions))
    return replace(
        analysis,
        headline=str(pack.get("headline") or analysis.headline).format(name=name),
        subtitle=str(pack.get("subtitle") or analysis.subtitle),
        services=services,
        service_descriptions=tuple(descriptions[: len(services)]),
        benefits=list(pack.get("benefits") or analysis.benefits),
        trust_points=list(pack.get("trust") or analysis.trust_points),
        about_text=str(pack.get("about") or analysis.about_text).format(name=name),
        cta_label=str(pack.get("cta") or analysis.cta_label),
        hours=str(pack.get("hours") or analysis.hours),
    )
