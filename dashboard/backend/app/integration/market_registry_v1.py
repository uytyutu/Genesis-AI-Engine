"""Global Market Database v1 — Stage 1 markets (30 countries).

Stage 2: unlisted countries map to regional_fallback models.
"""

from __future__ import annotations

from app.integration.market_registry_schema import (
    MarketIntelligenceMeta,
    MarketPriceRange,
    MarketProfile,
    ServicePricing,
    WebsiteProjectPricing,
    SERVICE_AI_EMPLOYEE,
    SERVICE_AUTOMATION,
    SERVICE_BRANDING,
    SERVICE_BUSINESS_PLAN,
    SERVICE_CHATBOT,
    SERVICE_CRM,
    SERVICE_DESKTOP_APP,
    SERVICE_GAME,
    SERVICE_MARKETING,
    SERVICE_MOBILE_APP,
    SERVICE_PRESENTATION,
    SERVICE_SEO,
)

# ISO codes — Stage 1
MARKET_DE = "DE"
MARKET_US = "US"
MARKET_CA = "CA"
MARKET_GB = "GB"
MARKET_FR = "FR"
MARKET_IT = "IT"
MARKET_ES = "ES"
MARKET_NL = "NL"
MARKET_BE = "BE"
MARKET_AT = "AT"
MARKET_CH = "CH"
MARKET_PL = "PL"
MARKET_CZ = "CZ"
MARKET_SK = "SK"
MARKET_HU = "HU"
MARKET_RO = "RO"
MARKET_UA = "UA"
MARKET_PT = "PT"
MARKET_RU = "RU"
MARKET_AU = "AU"
MARKET_NZ = "NZ"
MARKET_JP = "JP"
MARKET_KR = "KR"
MARKET_SG = "SG"
MARKET_AE = "AE"
MARKET_SA = "SA"
MARKET_ZA = "ZA"
MARKET_BR = "BR"
MARKET_MX = "MX"
MARKET_IN = "IN"
MARKET_DEFAULT = "DEFAULT"

STAGE1_MARKET_CODES: tuple[str, ...] = (
    MARKET_DE, MARKET_US, MARKET_CA, MARKET_GB, MARKET_FR, MARKET_IT, MARKET_ES,
    MARKET_NL, MARKET_BE, MARKET_AT, MARKET_CH, MARKET_PL, MARKET_CZ, MARKET_SK,
    MARKET_HU, MARKET_RO, MARKET_UA, MARKET_PT, MARKET_RU, MARKET_AU, MARKET_NZ,
    MARKET_JP, MARKET_KR, MARKET_SG, MARKET_AE, MARKET_SA, MARKET_ZA, MARKET_BR,
    MARKET_MX, MARKET_IN,
)


def _rng(frm: int, to: int, avg: int | None = None) -> MarketPriceRange:
    return MarketPriceRange(from_amount=frm, to_amount=to, average_market=avg or (frm + to) // 2)


def _scale_rng(r: MarketPriceRange, factor: float, *, round_to: int = 10) -> MarketPriceRange:
    def _r(v: int) -> int:
        return max(round_to, int(round(v * factor / round_to) * round_to))

    return _rng(_r(r.from_amount), _r(r.to_amount), _r(r.average_market))


def _de_website_projects() -> WebsiteProjectPricing:
    """Germany canonical bands (CEO reference)."""
    return WebsiteProjectPricing(
        landing_page=_rng(350, 490, 420),
        business_website=_rng(490, 590, 540),
        corporate_website=_rng(1190, 1890, 1540),
        online_store=_rng(890, 1190, 1040),
        restaurant_website=_rng(520, 720, 620),
        medical_website=_rng(680, 980, 830),
        real_estate_website=_rng(590, 890, 740),
        hotel_website=_rng(640, 940, 790),
        law_firm_website=_rng(720, 1020, 870),
        portfolio_website=_rng(380, 520, 450),
    )


def _de_services() -> dict[str, ServicePricing]:
    return {
        SERVICE_BUSINESS_PLAN: ServicePricing(_rng(350, 550, 450)),
        SERVICE_PRESENTATION: ServicePricing(_rng(200, 400, 300)),
        SERVICE_AUTOMATION: ServicePricing(_rng(600, 1200, 900)),
        SERVICE_AI_EMPLOYEE: ServicePricing(_rng(800, 1600, 1200)),
        SERVICE_CRM: ServicePricing(_rng(500, 1100, 800)),
        SERVICE_CHATBOT: ServicePricing(_rng(400, 900, 650)),
        SERVICE_MOBILE_APP: ServicePricing(_rng(2500, 6000, 4200)),
        SERVICE_DESKTOP_APP: ServicePricing(_rng(2000, 5000, 3500)),
        SERVICE_GAME: ServicePricing(_rng(5000, 15000, 10000)),
        SERVICE_MARKETING: ServicePricing(_rng(400, 900, 650)),
        SERVICE_SEO: ServicePricing(_rng(300, 700, 500)),
        SERVICE_BRANDING: ServicePricing(_rng(350, 800, 575)),
    }


def _meta(
    competition: str,
    factor: float,
    *,
    confidence: str = "high",
    last_review: str = "2026-07",
) -> MarketIntelligenceMeta:
    return MarketIntelligenceMeta(
        competition_level=competition,
        market_factor=factor,
        last_review=last_review,
        confidence=confidence,
    )


def _scale_rng_projects(wp: WebsiteProjectPricing, factor: float, *, round_to: int = 10) -> WebsiteProjectPricing:
    keys = (
        "landing_page", "business_website", "corporate_website", "online_store",
        "restaurant_website", "medical_website", "real_estate_website",
        "hotel_website", "law_firm_website", "portfolio_website",
    )
    return WebsiteProjectPricing(**{k: _scale_rng(getattr(wp, k), factor, round_to=round_to) for k in keys})


def _build_eur_market(
    code: str,
    names: dict[str, str],
    locale: str,
    legal: tuple[str, ...],
    requires: tuple[str, ...],
    factor: float,
    competition: str = "high",
) -> MarketProfile:
    wp = _scale_rng_projects(_de_website_projects(), factor)
    services = {k: ServicePricing(_scale_rng(v.standard, factor)) for k, v in _de_services().items()}
    return MarketProfile(
        code=code,
        names=names,
        currency="EUR",
        symbol="€",
        locale_default=locale,
        legal_requirements=legal,
        requires=requires,
        intelligence=_meta(competition, factor),
        website_projects=wp,
        services=services,
    )


def _build_market_v1() -> dict[str, MarketProfile]:
    markets: dict[str, MarketProfile] = {
        MARKET_DE: MarketProfile(
            code=MARKET_DE,
            names={"ru": "Германия", "en": "Germany", "de": "Deutschland"},
            currency="EUR",
            symbol="€",
            locale_default="de",
            legal_requirements=("Impressum", "Datenschutz"),
            requires=("impressum", "datenschutz", "gdpr"),
            intelligence=_meta("high", 1.0),
            website_projects=_de_website_projects(),
            services=_de_services(),
        ),
    }

    for code, names, loc, legal, req, factor, comp in [
        (MARKET_FR, {"ru": "Франция", "en": "France"}, "fr", ("Mentions légales", "RGPD"), ("mentions_legales", "rgpd"), 0.95, "high"),
        (MARKET_IT, {"ru": "Италия", "en": "Italy"}, "it", ("Privacy policy",), ("privacy", "gdpr"), 0.90, "high"),
        (MARKET_ES, {"ru": "Испания", "en": "Spain"}, "es", ("Aviso legal",), ("aviso_legal", "gdpr"), 0.85, "high"),
        (MARKET_NL, {"ru": "Нидерланды", "en": "Netherlands"}, "nl", ("Privacyverklaring",), ("gdpr",), 1.05, "high"),
        (MARKET_BE, {"ru": "Бельгия", "en": "Belgium"}, "fr", ("Mentions légales",), ("gdpr",), 1.0, "medium"),
        (MARKET_AT, {"ru": "Австрия", "en": "Austria"}, "de", ("Impressum", "Datenschutz"), ("impressum", "datenschutz", "gdpr"), 0.98, "high"),
        (MARKET_SK, {"ru": "Словакия", "en": "Slovakia"}, "sk", ("GDPR",), ("gdpr",), 0.62, "medium"),
        (MARKET_RO, {"ru": "Румыния", "en": "Romania"}, "ro", ("GDPR",), ("gdpr",), 0.58, "medium"),
        (MARKET_HU, {"ru": "Венгрия", "en": "Hungary"}, "hu", ("GDPR",), ("gdpr",), 0.60, "medium"),
        (MARKET_PT, {"ru": "Португалия", "en": "Portugal"}, "pt", ("Política de privacidade",), ("privacy", "gdpr"), 0.78, "medium"),
    ]:
        markets[code] = _build_eur_market(code, names, loc, legal, req, factor, comp)

    markets[MARKET_CH] = MarketProfile(
        code=MARKET_CH,
        names={"ru": "Швейцария", "en": "Switzerland"},
        currency="CHF", symbol="CHF", locale_default="de",
        legal_requirements=("Impressum", "Datenschutz"), requires=("impressum", "datenschutz"),
        intelligence=_meta("high", 1.35),
        website_projects=_scale_rng_projects(_de_website_projects(), 1.35, round_to=50),
        services={k: ServicePricing(_scale_rng(v.standard, 1.35, round_to=50)) for k, v in _de_services().items()},
    )

    us_wp = _scale_rng_projects(_de_website_projects(), 1.28)
    us_services = {k: ServicePricing(_scale_rng(v.standard, 1.28)) for k, v in _de_services().items()}
    markets[MARKET_US] = MarketProfile(
        code=MARKET_US, names={"ru": "США", "en": "United States"}, currency="USD", symbol="$",
        locale_default="en", legal_requirements=("Privacy Policy", "Terms of Service"),
        requires=("privacy_policy", "terms"), intelligence=_meta("high", 1.28),
        website_projects=us_wp, services=us_services,
    )
    markets[MARKET_CA] = MarketProfile(
        code=MARKET_CA, names={"ru": "Канада", "en": "Canada"}, currency="USD", symbol="$",
        locale_default="en", legal_requirements=("Privacy Policy",),
        requires=("privacy",), intelligence=_meta("high", 1.15),
        website_projects=_scale_rng_projects(_de_website_projects(), 1.15), services=us_services,
    )

    markets[MARKET_GB] = MarketProfile(
        code=MARKET_GB, names={"ru": "Великобритания", "en": "United Kingdom"}, currency="GBP", symbol="£",
        locale_default="en", legal_requirements=("Privacy Policy", "Cookie notice"),
        requires=("privacy", "cookies"), intelligence=_meta("high", 0.92),
        website_projects=_scale_rng_projects(_de_website_projects(), 0.92),
        services={k: ServicePricing(_scale_rng(v.standard, 0.92)) for k, v in _de_services().items()},
    )

    markets[MARKET_PL] = MarketProfile(
        code=MARKET_PL, names={"ru": "Польша", "en": "Poland"}, currency="PLN", symbol="zł",
        locale_default="pl", legal_requirements=("Polityka prywatności", "RODO"),
        requires=("rodo", "privacy"), intelligence=_meta("high", 0.72),
        website_projects=WebsiteProjectPricing(
            landing_page=_rng(1200, 1800, 1500), business_website=_rng(1800, 2800, 2300),
            corporate_website=_rng(4500, 7500, 6000), online_store=_rng(3500, 5500, 4500),
            restaurant_website=_rng(2000, 3200, 2600), medical_website=_rng(2800, 4200, 3500),
            real_estate_website=_rng(2200, 3600, 2900), hotel_website=_rng(2400, 3800, 3100),
            law_firm_website=_rng(2600, 4000, 3300), portfolio_website=_rng(1400, 2200, 1800),
        ),
        services={k: ServicePricing(_scale_rng(v.standard, 0.72, round_to=50)) for k, v in _de_services().items()},
    )

    markets[MARKET_CZ] = MarketProfile(
        code=MARKET_CZ, names={"ru": "Чехия", "en": "Czechia"}, currency="CZK", symbol="Kč",
        locale_default="cs", legal_requirements=("GDPR",), requires=("gdpr",),
        intelligence=_meta("medium", 0.68),
        website_projects=WebsiteProjectPricing(
            landing_page=_rng(15000, 24000, 19500), business_website=_rng(22000, 34000, 28000),
            corporate_website=_rng(55000, 90000, 72500), online_store=_rng(42000, 68000, 55000),
            restaurant_website=_rng(24000, 38000, 31000), medical_website=_rng(30000, 48000, 39000),
            real_estate_website=_rng(26000, 42000, 34000), hotel_website=_rng(28000, 44000, 36000),
            law_firm_website=_rng(32000, 50000, 41000), portfolio_website=_rng(16000, 26000, 21000),
        ),
        services={k: ServicePricing(_scale_rng(v.standard, 0.68, round_to=500)) for k, v in _de_services().items()},
    )

    markets[MARKET_UA] = MarketProfile(
        code=MARKET_UA, names={"ru": "Украина", "en": "Ukraine"}, currency="UAH", symbol="₴",
        locale_default="uk", legal_requirements=("Політика конфіденційності",), requires=("privacy",),
        intelligence=_meta("medium", 0.55),
        website_projects=WebsiteProjectPricing(
            landing_page=_rng(8000, 14000, 11000), business_website=_rng(12000, 18000, 15000),
            corporate_website=_rng(28000, 45000, 36500), online_store=_rng(22000, 36000, 29000),
            restaurant_website=_rng(14000, 22000, 18000), medical_website=_rng(18000, 28000, 23000),
            real_estate_website=_rng(15000, 24000, 19500), hotel_website=_rng(16000, 26000, 21000),
            law_firm_website=_rng(17000, 27000, 22000), portfolio_website=_rng(9000, 15000, 12000),
        ),
        services={k: ServicePricing(_scale_rng(v.standard, 0.55, round_to=500)) for k, v in _de_services().items()},
    )

    # RU: EUR for Stripe/Mission 1 (same checkout currency as outreach CIS B2B).
    markets[MARKET_RU] = MarketProfile(
        code=MARKET_RU,
        names={"ru": "Россия", "en": "Russia"},
        currency="EUR",
        symbol="€",
        locale_default="ru",
        legal_requirements=("Политика конфиденциальности",),
        requires=("privacy",),
        intelligence=_meta("medium", 0.52, confidence="medium"),
        website_projects=_scale_rng_projects(_de_website_projects(), 0.52),
        services={
            k: ServicePricing(_scale_rng(v.standard, 0.52)) for k, v in _de_services().items()
        },
    )

    markets[MARKET_AU] = MarketProfile(
        code=MARKET_AU, names={"ru": "Австралия", "en": "Australia"}, currency="AUD", symbol="A$",
        locale_default="en", legal_requirements=("Privacy Policy",), requires=("privacy",),
        intelligence=_meta("medium", 1.1),
        website_projects=_scale_rng_projects(_de_website_projects(), 1.1),
        services={k: ServicePricing(_scale_rng(v.standard, 1.1)) for k, v in _de_services().items()},
    )
    markets[MARKET_NZ] = MarketProfile(
        code=MARKET_NZ, names={"ru": "Новая Зеландия", "en": "New Zealand"}, currency="NZD", symbol="NZ$",
        locale_default="en", legal_requirements=("Privacy Act",), requires=("privacy",),
        intelligence=_meta("medium", 1.0),
        website_projects=_scale_rng_projects(_de_website_projects(), 1.0),
        services={k: ServicePricing(_scale_rng(v.standard, 1.0)) for k, v in _de_services().items()},
    )
    markets[MARKET_JP] = MarketProfile(
        code=MARKET_JP, names={"ru": "Япония", "en": "Japan"}, currency="JPY", symbol="¥",
        locale_default="ja", legal_requirements=("プライバシーポリシー",), requires=("privacy", "tokushoho"),
        intelligence=_meta("high", 1.2),
        website_projects=WebsiteProjectPricing(
            landing_page=_rng(60000, 90000, 75000), business_website=_rng(85000, 120000, 102500),
            corporate_website=_rng(180000, 280000, 230000), online_store=_rng(140000, 220000, 180000),
            restaurant_website=_rng(90000, 140000, 115000), medical_website=_rng(110000, 170000, 140000),
            real_estate_website=_rng(95000, 150000, 122500), hotel_website=_rng(100000, 160000, 130000),
            law_firm_website=_rng(105000, 165000, 135000), portfolio_website=_rng(70000, 110000, 90000),
        ),
        services={k: ServicePricing(_scale_rng(v.standard, 1.2, round_to=1000)) for k, v in _de_services().items()},
    )
    markets[MARKET_KR] = MarketProfile(
        code=MARKET_KR, names={"ru": "Южная Корея", "en": "South Korea"}, currency="KRW", symbol="₩",
        locale_default="ko", legal_requirements=("개인정보처리방침",), requires=("privacy",),
        intelligence=_meta("high", 1.05),
        website_projects=WebsiteProjectPricing(
            landing_page=_rng(450000, 700000, 575000), business_website=_rng(650000, 950000, 800000),
            corporate_website=_rng(1400000, 2200000, 1800000), online_store=_rng(1100000, 1700000, 1400000),
            restaurant_website=_rng(700000, 1100000, 900000), medical_website=_rng(850000, 1300000, 1075000),
            real_estate_website=_rng(750000, 1200000, 975000), hotel_website=_rng(800000, 1250000, 1025000),
            law_firm_website=_rng(820000, 1280000, 1050000), portfolio_website=_rng(500000, 800000, 650000),
        ),
        services={k: ServicePricing(_scale_rng(v.standard, 1.05, round_to=10000)) for k, v in _de_services().items()},
    )
    markets[MARKET_SG] = MarketProfile(
        code=MARKET_SG, names={"ru": "Сингапур", "en": "Singapore"}, currency="SGD", symbol="S$",
        locale_default="en", legal_requirements=("PDPA",), requires=("pdpa",), intelligence=_meta("high", 1.15),
        website_projects=_scale_rng_projects(_de_website_projects(), 1.15),
        services={k: ServicePricing(_scale_rng(v.standard, 1.15)) for k, v in _de_services().items()},
    )
    markets[MARKET_AE] = MarketProfile(
        code=MARKET_AE, names={"ru": "ОАЭ", "en": "UAE"}, currency="AED", symbol="AED",
        locale_default="en", legal_requirements=("Privacy policy",), requires=("privacy",),
        intelligence=_meta("high", 1.1),
        website_projects=_scale_rng_projects(_de_website_projects(), 1.1),
        services={k: ServicePricing(_scale_rng(v.standard, 1.1)) for k, v in _de_services().items()},
    )
    markets[MARKET_SA] = MarketProfile(
        code=MARKET_SA, names={"ru": "Саудовская Аравия", "en": "Saudi Arabia"}, currency="SAR", symbol="SAR",
        locale_default="ar", legal_requirements=("Privacy policy",), requires=("privacy",),
        intelligence=_meta("medium", 0.95),
        website_projects=_scale_rng_projects(_de_website_projects(), 0.95),
        services={k: ServicePricing(_scale_rng(v.standard, 0.95)) for k, v in _de_services().items()},
    )
    markets[MARKET_ZA] = MarketProfile(
        code=MARKET_ZA, names={"ru": "ЮАР", "en": "South Africa"}, currency="ZAR", symbol="R",
        locale_default="en", legal_requirements=("POPIA",), requires=("popia",),
        intelligence=_meta("medium", 0.75),
        website_projects=WebsiteProjectPricing(
            landing_page=_rng(6500, 11000, 8750), business_website=_rng(9000, 14000, 11500),
            corporate_website=_rng(22000, 35000, 28500), online_store=_rng(17000, 28000, 22500),
            restaurant_website=_rng(10000, 16000, 13000), medical_website=_rng(12000, 20000, 16000),
            real_estate_website=_rng(11000, 18000, 14500), hotel_website=_rng(11500, 19000, 15250),
            law_firm_website=_rng(12500, 20000, 16250), portfolio_website=_rng(7000, 12000, 9500),
        ),
        services={k: ServicePricing(_scale_rng(v.standard, 0.75, round_to=50)) for k, v in _de_services().items()},
    )
    markets[MARKET_BR] = MarketProfile(
        code=MARKET_BR, names={"ru": "Бразилия", "en": "Brazil"}, currency="BRL", symbol="R$",
        locale_default="pt", legal_requirements=("LGPD",), requires=("lgpd",),
        intelligence=_meta("medium", 0.70),
        website_projects=WebsiteProjectPricing(
            landing_page=_rng(2000, 3200, 2600), business_website=_rng(2800, 4200, 3500),
            corporate_website=_rng(7000, 11000, 9000), online_store=_rng(5500, 8500, 7000),
            restaurant_website=_rng(3200, 5000, 4100), medical_website=_rng(4000, 6500, 5250),
            real_estate_website=_rng(3500, 5500, 4500), hotel_website=_rng(3700, 5800, 4750),
            law_firm_website=_rng(3900, 6200, 5050), portfolio_website=_rng(2200, 3600, 2900),
        ),
        services={k: ServicePricing(_scale_rng(v.standard, 0.70, round_to=50)) for k, v in _de_services().items()},
    )
    markets[MARKET_MX] = MarketProfile(
        code=MARKET_MX, names={"ru": "Мексика", "en": "Mexico"}, currency="MXN", symbol="MX$",
        locale_default="es", legal_requirements=("Aviso de privacidad",), requires=("privacy",),
        intelligence=_meta("medium", 0.68),
        website_projects=WebsiteProjectPricing(
            landing_page=_rng(8500, 14000, 11250), business_website=_rng(12000, 18000, 15000),
            corporate_website=_rng(30000, 48000, 39000), online_store=_rng(24000, 38000, 31000),
            restaurant_website=_rng(14000, 22000, 18000), medical_website=_rng(17000, 28000, 22500),
            real_estate_website=_rng(15000, 25000, 20000), hotel_website=_rng(16000, 26000, 21000),
            law_firm_website=_rng(16500, 27000, 21750), portfolio_website=_rng(9500, 16000, 12750),
        ),
        services={k: ServicePricing(_scale_rng(v.standard, 0.68, round_to=500)) for k, v in _de_services().items()},
    )
    markets[MARKET_IN] = MarketProfile(
        code=MARKET_IN, names={"ru": "Индия", "en": "India"}, currency="INR", symbol="₹",
        locale_default="en", legal_requirements=("Privacy policy",), requires=("privacy",),
        intelligence=_meta("high", 0.45),
        website_projects=WebsiteProjectPricing(
            landing_page=_rng(25000, 45000, 35000), business_website=_rng(35000, 65000, 50000),
            corporate_website=_rng(120000, 220000, 170000), online_store=_rng(90000, 170000, 130000),
            restaurant_website=_rng(45000, 85000, 65000), medical_website=_rng(55000, 100000, 77500),
            real_estate_website=_rng(48000, 90000, 69000), hotel_website=_rng(50000, 95000, 72500),
            law_firm_website=_rng(52000, 98000, 75000), portfolio_website=_rng(28000, 52000, 40000),
        ),
        services={k: ServicePricing(_scale_rng(v.standard, 0.45, round_to=500)) for k, v in _de_services().items()},
    )

    markets[MARKET_DEFAULT] = MarketProfile(
        code=MARKET_DEFAULT,
        names={"ru": "международный рынок", "en": "international market"},
        currency="EUR", symbol="€", locale_default="en",
        legal_requirements=(), requires=(),
        intelligence=_meta("medium", 0.85, confidence="low"),
        website_projects=_scale_rng_projects(_de_website_projects(), 0.85),
        services={k: ServicePricing(_scale_rng(v.standard, 0.85)) for k, v in _de_services().items()},
        region_fallback="international",
    )
    return markets


MARKET_REGISTRY: dict[str, MarketProfile] = _build_market_v1()
