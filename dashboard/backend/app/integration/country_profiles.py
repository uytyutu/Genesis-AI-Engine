"""Country Profiles for Lead Engine farms — config, not hardcoded hunt logic.

CEO model: 1 country = 1 farm (independent quotas / stats / enable flags).
Lead collection: unlimited. Outreach send interval: 40–60s with country rotation.
Strict markets (DE and similar) use conservative send caps to reduce spam/ban risk.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# ---------------------------------------------------------------------------
# Tier map (commercial potential). Enable flags live in runtime config.
# ---------------------------------------------------------------------------

TIER_1 = ("DE", "US", "CA", "GB", "AT", "CH")
TIER_2 = ("NL", "BE", "FR", "IE", "AU")
TIER_3 = ("ES", "IT", "PL", "SE", "NO", "DK", "FI")
# CIS / East — language & price packs (CEO): UA, RU, KZ
TIER_CIS = ("UA", "RU", "KZ")
# APAC — night window for Europe (24/7 farm rotation)
TIER_APAC = ("AU", "NZ", "JP", "KR", "SG")

ALL_PROFILE_CODES: tuple[str, ...] = tuple(
    dict.fromkeys(TIER_1 + TIER_2 + TIER_3 + TIER_CIS + TIER_APAC)
)

# 24/7: Tier 1 + APAC (EN/JA/KO packs). Other EU Tier2/3 off until CEO toggles.
DEFAULT_ENABLED: frozenset[str] = frozenset(TIER_1 + TIER_APAC)

# Global send pacing (seconds between successful sends while rotating countries)
SEND_INTERVAL_MIN_SEC = 40
SEND_INTERVAL_MAX_SEC = 60


def _profile(
    *,
    code: str,
    name: str,
    tier: int,
    language: str,
    currency: str,
    timezone: str,
    email_template: str,
    prices: dict[str, Any],
    legal_notes: str,
    hunt_quota_daily: int,
    send_quota_daily: int,
    send_interval_sec: int,
    strict_anti_spam: bool = False,
    cities: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "name": name,
        "tier": tier,
        "enabled": code in DEFAULT_ENABLED,
        "language": language,
        "currency": currency,
        "timezone": timezone,
        "email_template": email_template,
        "prices": dict(_PRICES_DEPRECATED),  # SSOT: pricing_engine — do not read
        "legal_notes": legal_notes,
        "hunt_quota_daily": hunt_quota_daily,  # discovery soft budget (not a hard lead cap)
        "send_quota_daily": send_quota_daily,  # outreach — protective
        "send_interval_sec": send_interval_sec,
        "strict_anti_spam": strict_anti_spam,
        "cities": list(cities or []),
    }


# Shared Path A EUR anchors — DEPRECATED.
# Path A amounts live in ``pricing_engine._PATH_A_SKUS``. Profile ``prices``
# always points here; do not read amounts from country_profiles.
_PRICES_DEPRECATED: dict[str, Any] = {
    "deprecated": True,
    "ssot": "app.integration.pricing_engine",
}
_PRICES_EUR = _PRICES_DEPRECATED
_PRICES_USD = _PRICES_DEPRECATED
_PRICES_GBP = _PRICES_DEPRECATED
_PRICES_AUD = _PRICES_DEPRECATED
_PRICES_JPY = _PRICES_DEPRECATED
_PRICES_KRW = _PRICES_DEPRECATED
_PRICES_SGD = _PRICES_DEPRECATED
_PRICES_CIS = _PRICES_DEPRECATED


COUNTRY_PROFILES: dict[str, dict[str, Any]] = {
    # --- Tier 1 ---
    "DE": _profile(
        code="DE",
        name="Germany",
        tier=1,
        language="de",
        currency="EUR",
        timezone="Europe/Berlin",
        email_template="outreach_de_v1",
        prices=dict(_PRICES_EUR),
        legal_notes="UWG / GDPR strict. Impressum required. Conservative send caps.",
        hunt_quota_daily=500,
        send_quota_daily=40,
        send_interval_sec=55,
        strict_anti_spam=True,
        cities=[
            "Berlin", "Hamburg", "München", "Köln", "Frankfurt", "Stuttgart",
            "Düsseldorf", "Dortmund", "Essen", "Leipzig", "Bremen", "Dresden",
            "Hannover", "Nürnberg",
        ],
    ),
    "US": _profile(
        code="US",
        name="United States",
        tier=1,
        language="en",
        currency="USD",
        timezone="America/New_York",
        email_template="outreach_us_v1",
        prices=dict(_PRICES_USD),
        legal_notes="CAN-SPAM. Physical address in commercial email. Unsubscribe required.",
        hunt_quota_daily=800,
        send_quota_daily=60,
        send_interval_sec=45,
        cities=[
            "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
            "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Seattle",
        ],
    ),
    "CA": _profile(
        code="CA",
        name="Canada",
        tier=1,
        language="en",
        currency="CAD",
        timezone="America/Toronto",
        email_template="outreach_ca_v1",
        prices={**_PRICES_USD, "currency_note": "CAD display via market"},
        legal_notes="CASL — consent-oriented. Conservative cold outreach.",
        hunt_quota_daily=400,
        send_quota_daily=40,
        send_interval_sec=50,
        strict_anti_spam=True,
        cities=["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa", "Edmonton"],
    ),
    "GB": _profile(
        code="GB",
        name="United Kingdom",
        tier=1,
        language="en",
        currency="GBP",
        timezone="Europe/London",
        email_template="outreach_gb_v1",
        prices=dict(_PRICES_GBP),
        legal_notes="PECR / UK GDPR. Soft opt-in culture — moderate caps.",
        hunt_quota_daily=500,
        send_quota_daily=45,
        send_interval_sec=50,
        strict_anti_spam=True,
        cities=["London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Edinburgh", "Bristol"],
    ),
    "AT": _profile(
        code="AT",
        name="Austria",
        tier=1,
        language="de",
        currency="EUR",
        timezone="Europe/Vienna",
        email_template="outreach_at_v1",
        prices=dict(_PRICES_EUR),
        legal_notes="Similar to DE (UWG-like / GDPR). Keep DE-like pacing.",
        hunt_quota_daily=200,
        send_quota_daily=25,
        send_interval_sec=55,
        strict_anti_spam=True,
        cities=["Wien", "Graz", "Linz", "Salzburg", "Innsbruck"],
    ),
    "CH": _profile(
        code="CH",
        name="Switzerland",
        tier=1,
        language="de",
        currency="CHF",
        timezone="Europe/Zurich",
        email_template="outreach_ch_v1",
        prices={**_PRICES_EUR, "currency_note": "CHF via market"},
        legal_notes="nFADP. Conservative B2B outreach.",
        hunt_quota_daily=200,
        send_quota_daily=25,
        send_interval_sec=55,
        strict_anti_spam=True,
        cities=["Zürich", "Genève", "Basel", "Bern", "Lausanne"],
    ),
    # --- Tier 2 ---
    "NL": _profile(
        code="NL", name="Netherlands", tier=2, language="nl", currency="EUR",
        timezone="Europe/Amsterdam", email_template="outreach_nl_v1", prices=dict(_PRICES_EUR),
        legal_notes="GDPR / Telecommunicatiewet.", hunt_quota_daily=250, send_quota_daily=30,
        send_interval_sec=50, cities=["Amsterdam", "Rotterdam", "Den Haag", "Utrecht", "Eindhoven"],
    ),
    "BE": _profile(
        code="BE", name="Belgium", tier=2, language="nl", currency="EUR",
        timezone="Europe/Brussels", email_template="outreach_be_v1", prices=dict(_PRICES_EUR),
        legal_notes="GDPR. FR/NL language split — template by city later.",
        hunt_quota_daily=200, send_quota_daily=25, send_interval_sec=50,
        cities=["Bruxelles", "Antwerpen", "Gent", "Charleroi", "Liège"],
    ),
    "FR": _profile(
        code="FR", name="France", tier=2, language="fr", currency="EUR",
        timezone="Europe/Paris", email_template="outreach_fr_v1", prices=dict(_PRICES_EUR),
        legal_notes="CNIL / GDPR. Soft approach.", hunt_quota_daily=300, send_quota_daily=30,
        send_interval_sec=50, cities=["Paris", "Lyon", "Marseille", "Toulouse", "Lille", "Bordeaux"],
    ),
    "IE": _profile(
        code="IE", name="Ireland", tier=2, language="en", currency="EUR",
        timezone="Europe/Dublin", email_template="outreach_ie_v1", prices=dict(_PRICES_EUR),
        legal_notes="GDPR.", hunt_quota_daily=150, send_quota_daily=20, send_interval_sec=50,
        cities=["Dublin", "Cork", "Galway", "Limerick"],
    ),
    "AU": _profile(
        code="AU", name="Australia", tier=2, language="en", currency="AUD",
        timezone="Australia/Sydney", email_template="outreach_au_v1",
        prices=dict(_PRICES_AUD), legal_notes="Spam Act 2003 — consent bias.",
        hunt_quota_daily=250, send_quota_daily=30, send_interval_sec=50, strict_anti_spam=True,
        cities=["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
    ),
    # --- Tier 3 ---
    "ES": _profile(
        code="ES", name="Spain", tier=3, language="es", currency="EUR",
        timezone="Europe/Madrid", email_template="outreach_es_v1", prices=dict(_PRICES_EUR),
        legal_notes="GDPR / LSSI.", hunt_quota_daily=200, send_quota_daily=25, send_interval_sec=45,
        cities=["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao"],
    ),
    "IT": _profile(
        code="IT", name="Italy", tier=3, language="it", currency="EUR",
        timezone="Europe/Rome", email_template="outreach_it_v1", prices=dict(_PRICES_EUR),
        legal_notes="GDPR / Codice Privacy.", hunt_quota_daily=200, send_quota_daily=25,
        send_interval_sec=45, cities=["Roma", "Milano", "Napoli", "Torino", "Firenze"],
    ),
    "PL": _profile(
        code="PL", name="Poland", tier=3, language="pl", currency="PLN",
        timezone="Europe/Warsaw", email_template="outreach_pl_v1",
        prices={**_PRICES_EUR, "currency_note": "PLN"}, legal_notes="GDPR.",
        hunt_quota_daily=250, send_quota_daily=30, send_interval_sec=45,
        cities=["Warszawa", "Kraków", "Wrocław", "Gdańsk", "Poznań"],
    ),
    "SE": _profile(
        code="SE", name="Sweden", tier=3, language="sv", currency="SEK",
        timezone="Europe/Stockholm", email_template="outreach_se_v1",
        prices={**_PRICES_EUR, "currency_note": "SEK"}, legal_notes="GDPR / marketing law.",
        hunt_quota_daily=150, send_quota_daily=20, send_interval_sec=50, strict_anti_spam=True,
        cities=["Stockholm", "Göteborg", "Malmö"],
    ),
    "NO": _profile(
        code="NO", name="Norway", tier=3, language="no", currency="NOK",
        timezone="Europe/Oslo", email_template="outreach_no_v1",
        prices={**_PRICES_EUR, "currency_note": "NOK"}, legal_notes="Marketing Control Act.",
        hunt_quota_daily=120, send_quota_daily=15, send_interval_sec=55, strict_anti_spam=True,
        cities=["Oslo", "Bergen", "Trondheim"],
    ),
    "DK": _profile(
        code="DK", name="Denmark", tier=3, language="da", currency="DKK",
        timezone="Europe/Copenhagen", email_template="outreach_dk_v1",
        prices={**_PRICES_EUR, "currency_note": "DKK"}, legal_notes="Marketing Practices Act.",
        hunt_quota_daily=120, send_quota_daily=15, send_interval_sec=55, strict_anti_spam=True,
        cities=["København", "Aarhus", "Odense"],
    ),
    "FI": _profile(
        code="FI", name="Finland", tier=3, language="fi", currency="EUR",
        timezone="Europe/Helsinki", email_template="outreach_fi_v1", prices=dict(_PRICES_EUR),
        legal_notes="GDPR.", hunt_quota_daily=120, send_quota_daily=15, send_interval_sec=55,
        cities=["Helsinki", "Tampere", "Turku"],
    ),
    # --- CIS (CEO) ---
    "UA": _profile(
        code="UA",
        name="Ukraine",
        tier=2,
        language="uk",
        currency="UAH",
        timezone="Europe/Kyiv",
        email_template="outreach_ua_v1",
        prices=dict(_PRICES_CIS),
        legal_notes="Local marketing norms + careful personal data. Prefer company emails.",
        hunt_quota_daily=300,
        send_quota_daily=40,
        send_interval_sec=45,
        cities=["Київ", "Львів", "Одеса", "Харків", "Дніпро"],
    ),
    "RU": _profile(
        code="RU",
        name="Russia",
        tier=2,
        language="ru",
        currency="RUB",
        timezone="Europe/Moscow",
        email_template="outreach_ru_v1",
        prices=dict(_PRICES_CIS),
        legal_notes="152-FZ personal data. Company public contacts only.",
        hunt_quota_daily=400,
        send_quota_daily=50,
        send_interval_sec=45,
        cities=["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань"],
    ),
    "KZ": _profile(
        code="KZ",
        name="Kazakhstan",
        tier=2,
        language="ru",
        currency="KZT",
        timezone="Asia/Almaty",
        email_template="outreach_kz_v1",
        prices=dict(_PRICES_CIS),
        legal_notes="Public business contacts. RU/KK language templates later.",
        hunt_quota_daily=200,
        send_quota_daily=30,
        send_interval_sec=45,
        cities=["Алматы", "Астана", "Шымкент", "Караганда"],
    ),
    # --- APAC (24/7 night window for Europe) ---
    "NZ": _profile(
        code="NZ",
        name="New Zealand",
        tier=2,
        language="en",
        currency="NZD",
        timezone="Pacific/Auckland",
        email_template="outreach_nz_v1",
        prices={**_PRICES_AUD, "currency_note": "NZD"},
        legal_notes="Unsolicited Electronic Messages Act — consent bias.",
        hunt_quota_daily=150,
        send_quota_daily=20,
        send_interval_sec=55,
        strict_anti_spam=True,
        cities=["Auckland", "Wellington", "Christchurch", "Hamilton"],
    ),
    "JP": _profile(
        code="JP",
        name="Japan",
        tier=2,
        language="ja",
        currency="JPY",
        timezone="Asia/Tokyo",
        email_template="outreach_jp_v1",
        prices=dict(_PRICES_JPY),
        legal_notes="Act on Specified Commercial Transactions / careful B2B cold mail.",
        hunt_quota_daily=200,
        send_quota_daily=20,
        send_interval_sec=55,
        strict_anti_spam=True,
        cities=["Tokyo", "Osaka", "Yokohama", "Nagoya", "Fukuoka", "Sapporo"],
    ),
    "KR": _profile(
        code="KR",
        name="South Korea",
        tier=2,
        language="ko",
        currency="KRW",
        timezone="Asia/Seoul",
        email_template="outreach_kr_v1",
        prices=dict(_PRICES_KRW),
        legal_notes="Information and Communications Network Act — conservative B2B.",
        hunt_quota_daily=180,
        send_quota_daily=18,
        send_interval_sec=55,
        strict_anti_spam=True,
        cities=["Seoul", "Busan", "Incheon", "Daegu", "Daejeon"],
    ),
    "SG": _profile(
        code="SG",
        name="Singapore",
        tier=2,
        language="en",
        currency="SGD",
        timezone="Asia/Singapore",
        email_template="outreach_sg_v1",
        prices=dict(_PRICES_SGD),
        legal_notes="PDPA / Spam Control Act — consent-oriented B2B.",
        hunt_quota_daily=120,
        send_quota_daily=15,
        send_interval_sec=55,
        strict_anti_spam=True,
        cities=["Singapore"],
    ),
}


def default_runtime_config() -> dict[str, Any]:
    """Serializable farm config: enable flags + global pacing. Lead cap = unlimited."""
    return {
        "version": 1,
        "lead_cap": None,  # unlimited
        "send_interval_min_sec": SEND_INTERVAL_MIN_SEC,
        "send_interval_max_sec": SEND_INTERVAL_MAX_SEC,
        "rotate_countries": True,
        "enabled_countries": sorted(DEFAULT_ENABLED),
        "profiles": {code: deepcopy(COUNTRY_PROFILES[code]) for code in ALL_PROFILE_CODES},
    }


def merge_runtime_config(stored: dict[str, Any] | None) -> dict[str, Any]:
    base = default_runtime_config()
    if not stored or not isinstance(stored, dict):
        return base
    out = deepcopy(base)
    if "enabled_countries" in stored and isinstance(stored["enabled_countries"], list):
        codes = [
            str(c).strip().upper()[:2]
            for c in stored["enabled_countries"]
            if str(c).strip().upper()[:2] in COUNTRY_PROFILES
        ]
        out["enabled_countries"] = codes or list(DEFAULT_ENABLED)
    for key in ("send_interval_min_sec", "send_interval_max_sec", "rotate_countries", "lead_cap"):
        if key in stored:
            out[key] = stored[key]
    # Clamp intervals into safe band
    try:
        out["send_interval_min_sec"] = max(
            40, min(60, int(out.get("send_interval_min_sec") or SEND_INTERVAL_MIN_SEC))
        )
        out["send_interval_max_sec"] = max(
            out["send_interval_min_sec"],
            min(90, int(out.get("send_interval_max_sec") or SEND_INTERVAL_MAX_SEC)),
        )
    except (TypeError, ValueError):
        out["send_interval_min_sec"] = SEND_INTERVAL_MIN_SEC
        out["send_interval_max_sec"] = SEND_INTERVAL_MAX_SEC
    # Per-country enable overlay
    stored_profiles = stored.get("profiles") if isinstance(stored.get("profiles"), dict) else {}
    for code, prof in out["profiles"].items():
        prof["enabled"] = code in out["enabled_countries"]
        patch = stored_profiles.get(code) if isinstance(stored_profiles.get(code), dict) else {}
        for k in ("send_quota_daily", "hunt_quota_daily", "send_interval_sec", "enabled"):
            if k in patch:
                prof[k] = patch[k]
        if "enabled" in patch:
            # keep enabled_countries in sync
            if patch["enabled"] and code not in out["enabled_countries"]:
                out["enabled_countries"].append(code)
            if not patch["enabled"] and code in out["enabled_countries"]:
                out["enabled_countries"] = [c for c in out["enabled_countries"] if c != code]
    out["enabled_countries"] = sorted(set(out["enabled_countries"]))
    return out


def enabled_profiles(cfg: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    runtime = merge_runtime_config(cfg)
    enabled = set(runtime.get("enabled_countries") or [])
    rows = [runtime["profiles"][c] for c in ALL_PROFILE_CODES if c in enabled]
    rows.sort(key=lambda r: (int(r.get("tier") or 9), str(r.get("code") or "")))
    return rows


def get_profile(code: str, cfg: dict[str, Any] | None = None) -> dict[str, Any] | None:
    runtime = merge_runtime_config(cfg)
    c = str(code or "").strip().upper()[:2]
    return runtime["profiles"].get(c)
