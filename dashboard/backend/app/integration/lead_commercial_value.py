"""Lead Priority — commercial value for Virtus Core Acquisition.

Goal: rank by expected commercial value, not «easy cheap Basic wins».

Lead Priority =
  Business Potential × Website Need × Package Fit × Win Probability

Business Potential (softened) =
  Industry Prior + Review Quality + Business Signals + Website Signals

Industry prior alone must NOT auto-qualify Premium (e.g. bare dental < 0.78).
"""

from __future__ import annotations

from typing import Any

from app.integration.lead_pipeline_service import detect_niche_key

# Path A EUR list prices (display / EV math). Local currency applied later in prepare.
_PACKAGE_EUR = {"basic": 350.0, "business": 650.0, "premium": 1200.0}
_PACKAGE_FIT = {"basic": 0.35, "business": 0.65, "premium": 1.0}

# Soft industry priors — ceiling for niche alone stays below Premium gate (0.78).
_NICHE_POTENTIAL: dict[str, float] = {
    "zahnarzt": 0.58,
    "clinic": 0.56,
    "cosmetic": 0.55,
    "legal": 0.57,
    "solar": 0.55,
    "accounting": 0.54,
    "architect": 0.53,
    "finance": 0.56,
    "auto_dealer": 0.54,
    "hotel": 0.52,
    "real_estate": 0.53,
    "manufacturing": 0.54,
    "engineering": 0.53,
    "kfz": 0.42,
    "dach": 0.40,
    "plumber": 0.28,
    "handwerk": 0.32,
    "cafe": 0.34,
    "general": 0.38,
}

_HIGH_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("zahn", "dental", "stomat", "orthodont", "kieferorth"), "zahnarzt"),
    (("cosmetic", "ästhetisch", "aesthet", "schönheits", "beauty clinic", "botox"), "cosmetic"),
    (("klinik", "clinic", "arztpraxis", "praxis", "hospital", "medizin", "physio"), "clinic"),
    (("anwalt", "rechtsanwalt", "notariat", "law firm", "solicitor", "юрист", "lawyer", "attorney"), "legal"),
    (("solar", "photovolta", "pv-anlage", "wärmepumpe", "heat pump", "солнечн"), "solar"),
    (("steuerberater", "buchhalter", "accountant", "accounting", "wirtschaftsprüfer", "бухгалтер"), "accounting"),
    (("architekt", "architect", "architectural"), "architect"),
    (("finanzberater", "financial advisor", "wealth", "vermögensberater", "independent advisor"), "finance"),
    (("autohaus", "car dealer", "bmw", "mercedes", "audi händler"), "auto_dealer"),
    (("hotel", "resort", "spa hotel", "motel"), "hotel"),
    (("immobil", "real estate", "makler", "realtor", "estate agent"), "real_estate"),
    (("fertigung", "manufacturing", "produktion", "factory", "завод"), "manufacturing"),
    (("ingenieurwesen", "engineering firm", "машиностроен", "mechanical engineer"), "engineering"),
    (("sanitär", "sanitaer", "plumber", "klempner", "rohrreinigung", "сантехн"), "plumber"),
    (("handwerk", "schlüsseldienst", "reinigung", "gärtner"), "handwerk"),
]


def _clamp01(x: float, lo: float = 0.15, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(x)))


def classify_commercial_niche(row: dict[str, Any]) -> str:
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    blob = " ".join(
        [
            str(row.get("company_name") or ""),
            str(row.get("fit_reason") or ""),
            str(meta.get("niche") or ""),
            str(meta.get("hunt_query") or ""),
            str(meta.get("types") or ""),
            str(meta.get("place_types") or ""),
        ]
    ).casefold()
    for keys, niche in _HIGH_KEYWORDS:
        if any(k in blob for k in keys):
            return niche
    detected = detect_niche_key(
        company=str(row.get("company_name") or ""),
        query=str(meta.get("hunt_query") or ""),
        meta=meta,
    )
    return detected if detected in _NICHE_POTENTIAL else "general"


def _review_quality(meta: dict[str, Any]) -> tuple[float, list[str]]:
    reasons: list[str] = []
    reviews = meta.get("review_count") or meta.get("user_rating_count") or meta.get("ratings_total")
    try:
        n_reviews = int(reviews or 0)
    except (TypeError, ValueError):
        n_reviews = 0
    rating = meta.get("rating") or meta.get("user_rating")
    try:
        r = float(rating) if rating is not None else 0.0
    except (TypeError, ValueError):
        r = 0.0

    score = 0.0
    if n_reviews >= 200:
        score += 0.18
        reasons.append(f"Отзывы {n_reviews}+ → масштаб")
    elif n_reviews >= 80:
        score += 0.12
        reasons.append(f"Отзывы {n_reviews}")
    elif n_reviews >= 25:
        score += 0.07
        reasons.append(f"Отзывы {n_reviews}")
    elif n_reviews >= 8:
        score += 0.03
        reasons.append(f"Отзывы {n_reviews}")

    if r >= 4.5 and n_reviews >= 25:
        score += 0.06
        reasons.append(f"Рейтинг {r:.1f} при объёме")
    elif r >= 4.2 and n_reviews >= 10:
        score += 0.03
        reasons.append(f"Рейтинг {r:.1f}")

    return min(0.25, score), reasons


def _business_signals(row: dict[str, Any], meta: dict[str, Any]) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0
    types = str(meta.get("types") or meta.get("place_types") or "").casefold()
    if any(
        t in types
        for t in (
            "hospital",
            "university",
            "car_dealer",
            "lawyer",
            "dentist",
            "real_estate_agency",
            "accounting",
            "electrician",
        )
    ):
        score += 0.05
        reasons.append("Google Places type = крупный сегмент")

    name = str(row.get("company_name") or "")
    if any(w in name for w in (" GmbH", " AG", " Ltd", " Inc", " Group", " Klinik", " Partners", " LLP", " PLC")):
        score += 0.06
        reasons.append("Признак юр. масштаба в названии")

    if meta.get("place_id") and (meta.get("address") or meta.get("formatted_address")):
        score += 0.02
        reasons.append("Полный Places-профиль")

    return min(0.20, score), reasons


def _website_signals_for_bp(row: dict[str, Any], analysis: dict[str, Any] | None) -> tuple[float, list[str]]:
    """Positive scale signals of online presence — not Website Need (brokenness)."""
    reasons: list[str] = []
    score = 0.0
    url = str(row.get("website_url") or "").strip()
    analysis = analysis if isinstance(analysis, dict) else {}
    if not analysis:
        existing = row.get("site_analysis")
        analysis = existing if isinstance(existing, dict) else {}

    if url:
        score += 0.04
        reasons.append("Есть сайт")
        host = url.casefold()
        if not any(x in host for x in ("wixsite", "squarespace", "blogspot", "wordpress.com", "jimdo")):
            score += 0.03
            reasons.append("Свой домен (не конструктор)")
        else:
            reasons.append("Сайт на конструкторе")
    else:
        reasons.append("Нет сайта — без web-сигнала масштаба")

    # Light positive: site exists and is not a total wreck → established presence
    issue_count = int(analysis.get("issue_count") or len(analysis.get("issues") or []) or 0)
    if url and issue_count <= 2:
        score += 0.04
        reasons.append("Сайт относительно цельный (мало багов) → живой бизнес")
    elif url and issue_count <= 4:
        score += 0.02

    return min(0.15, score), reasons


def score_business_potential(
    row: dict[str, Any],
    *,
    analysis: dict[str, Any] | None = None,
) -> tuple[float, list[str]]:
    """Industry prior + reviews + business signals + website signals.

    Soft priors: dental alone (~0.58) cannot clear Premium gate (0.78) without signals.
    """
    reasons: list[str] = []
    niche = classify_commercial_niche(row)
    industry = _NICHE_POTENTIAL.get(niche, 0.38)
    reasons.append(f"Industry prior «{niche}»={industry:.2f}")

    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    review_s, review_r = _review_quality(meta)
    biz_s, biz_r = _business_signals(row, meta)
    web_s, web_r = _website_signals_for_bp(row, analysis)

    total = industry + review_s + biz_s + web_s
    reasons.extend(review_r)
    reasons.extend(biz_r)
    reasons.extend(web_r)
    reasons.append(
        f"BP = {industry:.2f}+{review_s:.2f}+{biz_s:.2f}+{web_s:.2f} → {_clamp01(total):.2f}"
    )
    return _clamp01(total), reasons[:8]


def score_website_need(row: dict[str, Any], analysis: dict[str, Any] | None) -> tuple[float, list[str]]:
    """How badly the online presence needs work — not business size."""
    reasons: list[str] = []
    fit = (row.get("fit_reason") or "").casefold()
    url = str(row.get("website_url") or "").strip()
    analysis = analysis if isinstance(analysis, dict) else {}
    if not analysis:
        existing = row.get("site_analysis")
        analysis = existing if isinstance(existing, dict) else {}

    if not url or "нет сайта" in fit or "no website" in fit or "ohne website" in fit:
        return _clamp01(0.95), ["Нет сайта — максимальная потребность"]

    issue_count = int(analysis.get("issue_count") or len(analysis.get("issues") or []) or 0)
    imp = int(analysis.get("improvement_score") or 0)

    need = 0.25
    if issue_count >= 6:
        need = 0.92
        reasons.append(f"{issue_count} проблем на сайте")
    elif issue_count >= 4:
        need = 0.75
        reasons.append(f"{issue_count} проблем")
    elif issue_count >= 2:
        need = 0.55
        reasons.append(f"{issue_count} проблемы")
    elif issue_count == 1:
        need = 0.40
        reasons.append("1 заметная проблема")
    else:
        need = 0.28
        reasons.append("Сайт есть, явных проблем мало")

    if imp >= 70:
        need = max(need, 0.85)
        reasons.append(f"improvement_score {imp}")
    elif imp >= 45:
        need = max(need, 0.60)

    issues = [str(i).casefold() for i in (analysis.get("issues") or [])]
    if any("https" in i or "mobil" in i or "veraltet" in i for i in issues):
        need = min(1.0, need + 0.08)
        reasons.append("Критичные сигналы (HTTPS / mobile / устарело)")

    return _clamp01(need), reasons[:5]


def recommend_package_id(
    business_potential: float,
    website_need: float,
) -> tuple[str, str]:
    """Package from business potential first; website need can upgrade, not force Basic on high-LTV.

    Mid-band Premium requires stronger BP (reviews/signals), not soft industry prior alone.
    """
    bp = float(business_potential)
    wn = float(website_need)

    if bp >= 0.78:
        return "premium", "Высокий потенциал бизнеса → Premium (независимо от малого числа багов сайта)"
    # Raised from 0.62/0.45 so bare dental (~0.58–0.70 prior+web) lands Business, not auto-Premium.
    if bp >= 0.70 and wn >= 0.50:
        return "premium", "Сильный бизнес (сигналы) + реальная потребность сайта → Premium"
    if bp >= 0.62:
        return "business", "Сильный/средний потенциал без полного Premium-сигнала → Business"
    if bp >= 0.48:
        if wn >= 0.70:
            return "business", "Средний потенциал + сильная потребность сайта → Business"
        return "business", "Средний потенциал → Business"
    if wn >= 0.85 and bp >= 0.30:
        return "business", "Слабый/средний бизнес, но сайт критичен → Business (не Basic-ловушка)"
    if wn >= 0.55:
        return "basic", "Локальный масштаб + умеренная потребность → Basic"
    return "basic", "Низкий потенциал / слабая потребность → Basic"


def package_fit_factor(package_id: str) -> float:
    return _PACKAGE_FIT.get(package_id, _PACKAGE_FIT["basic"])


def compute_lead_priority(
    row: dict[str, Any],
    *,
    analysis: dict[str, Any] | None = None,
    win_probability_pct: int | None = None,
) -> dict[str, Any]:
    """Multiplicative Lead Priority + package recommendation."""
    bp, bp_reasons = score_business_potential(row, analysis=analysis)
    wn, wn_reasons = score_website_need(row, analysis)
    package_id, pkg_rationale = recommend_package_id(bp, wn)
    pf = package_fit_factor(package_id)

    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    if win_probability_pct is None:
        try:
            win_probability_pct = int(meta.get("win_probability_pct") or 0)
        except (TypeError, ValueError):
            win_probability_pct = 0
    if win_probability_pct <= 0:
        win_probability_pct = 40

    win_n = _clamp01(win_probability_pct / 100.0, lo=0.12, hi=1.0)
    priority = bp * wn * pf * win_n
    price = _PACKAGE_EUR.get(package_id, 350.0)
    expected_eur = round(price * (win_probability_pct / 100.0), 2)

    return {
        "lead_priority": round(priority, 4),
        "business_potential": round(bp, 3),
        "website_need": round(wn, 3),
        "package_fit": round(pf, 3),
        "win_probability_pct": int(win_probability_pct),
        "win_factor": round(win_n, 3),
        "recommended_package_id": package_id,
        "package_price_eur": price,
        "expected_value_eur": expected_eur,
        "pricing_rationale": pkg_rationale,
        "niche": classify_commercial_niche(row),
        "reasons": {
            "business_potential": bp_reasons,
            "website_need": wn_reasons,
        },
        "formula_ru": "Lead Priority = Business Potential × Website Need × Package Fit × Win%",
    }
