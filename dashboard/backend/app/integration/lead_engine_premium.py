"""Premium Scoring + Smart Offer Selection (Lead Engine v1).

Separate from frozen Acquisition Scoring v1 (Lead Priority). This layer ranks
outreach urgency and chooses Basic / Business / Repair / skip-healthy.
"""

from __future__ import annotations

from typing import Any

# Point weights (plan)
_WEIGHTS = {
    "website_broken": 35,
    "no_ssl": 10,
    "mobile_broken": 15,
    "slow_website": 10,
    "no_google_business": 10,
    "no_reviews": 5,
    "old_design": 10,
    "no_cta": 10,
    "no_website": 40,
}


def _analysis(row: dict[str, Any], analysis: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(analysis, dict) and analysis:
        return analysis
    existing = row.get("site_analysis")
    return existing if isinstance(existing, dict) else {}


def _issues_blob(analysis: dict[str, Any]) -> str:
    parts = [str(i) for i in (analysis.get("issues") or [])]
    parts.extend(str(s) for s in (analysis.get("strengths") or [])[:0])
    tech = analysis.get("tech_stack") or analysis.get("findings") or []
    if isinstance(tech, list):
        parts.extend(str(t) for t in tech)
    return " ".join(parts).casefold()


def compute_premium_score(
    row: dict[str, Any],
    *,
    analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return premium_score + breakdown for Ready queue ranking."""
    analysis = _analysis(row, analysis)
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    url = str(row.get("website_url") or "").strip()
    fit = str(row.get("fit_reason") or "").casefold()
    blob = _issues_blob(analysis)
    breakdown: dict[str, int] = {}
    total = 0

    no_site = (
        not url
        or "нет сайта" in fit
        or "no website" in fit
        or "ohne website" in fit
        or bool(meta.get("no_website"))
    )
    if no_site:
        breakdown["no_website"] = _WEIGHTS["no_website"]
        total += _WEIGHTS["no_website"]
        return {
            "premium_score": total,
            "breakdown": breakdown,
            "signals": list(breakdown.keys()),
        }

    fetch_ok = analysis.get("fetch_ok")
    if fetch_ok is False or "unreachable" in blob or "timeout" in blob or "offline" in blob:
        breakdown["website_broken"] = _WEIGHTS["website_broken"]
        total += _WEIGHTS["website_broken"]

    if (
        "https" in blob
        or "ssl" in blob
        or "kein https" in blob
        or analysis.get("https") is False
        or (url.startswith("http://"))
    ):
        breakdown["no_ssl"] = _WEIGHTS["no_ssl"]
        total += _WEIGHTS["no_ssl"]

    if "mobil" in blob or "mobile" in blob or "viewport" in blob:
        breakdown["mobile_broken"] = _WEIGHTS["mobile_broken"]
        total += _WEIGHTS["mobile_broken"]

    if "langsam" in blob or "slow" in blob or "performance" in blob or "lcp" in blob:
        breakdown["slow_website"] = _WEIGHTS["slow_website"]
        total += _WEIGHTS["slow_website"]

    if meta.get("has_google_business") is False or "kein google" in blob or "no google business" in blob:
        breakdown["no_google_business"] = _WEIGHTS["no_google_business"]
        total += _WEIGHTS["no_google_business"]

    rating = meta.get("rating")
    reviews = meta.get("user_ratings_total") or meta.get("reviews_count")
    try:
        rev_n = int(reviews or 0)
    except (TypeError, ValueError):
        rev_n = 0
    if meta.get("place_id") and rev_n == 0:
        breakdown["no_reviews"] = _WEIGHTS["no_reviews"]
        total += _WEIGHTS["no_reviews"]

    if "veraltet" in blob or "outdated" in blob or "old design" in blob or "устарел" in blob:
        breakdown["old_design"] = _WEIGHTS["old_design"]
        total += _WEIGHTS["old_design"]

    if "cta" in blob or "call to action" in blob or "kein kontakt" in blob:
        breakdown["no_cta"] = _WEIGHTS["no_cta"]
        total += _WEIGHTS["no_cta"]

    issue_count = int(analysis.get("issue_count") or len(analysis.get("issues") or []) or 0)
    if issue_count >= 6 and "website_broken" not in breakdown:
        breakdown["website_broken"] = _WEIGHTS["website_broken"]
        total += _WEIGHTS["website_broken"]

    return {
        "premium_score": int(total),
        "breakdown": breakdown,
        "signals": list(breakdown.keys()),
    }


def select_smart_offer(
    row: dict[str, Any],
    *,
    analysis: dict[str, Any] | None = None,
    premium: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Choose Website Basic / Business / Repair / skip healthy."""
    analysis = _analysis(row, analysis)
    premium = premium or compute_premium_score(row, analysis=analysis)
    score = int(premium.get("premium_score") or 0)
    signals = set(premium.get("signals") or [])
    url = str(row.get("website_url") or "").strip()
    fit = str(row.get("fit_reason") or "").casefold()
    no_site = (
        not url
        or "нет сайта" in fit
        or "no website" in fit
        or "ohne website" in fit
        or "no_website" in signals
    )

    if no_site:
        return {
            "offer_kind": "website",
            "recommended_package_id": "basic",
            "skip_outreach": False,
            "skip_reason": None,
            "rationale": "No website → Website Basic",
        }

    if "website_broken" in signals or score >= 50:
        pkg = "repair_standard" if score >= 60 else "repair_lite"
        return {
            "offer_kind": "repair",
            "recommended_package_id": pkg,
            "skip_outreach": False,
            "skip_reason": None,
            "rationale": f"Serious site problems (score={score}) → Repair",
        }

    if "old_design" in signals or score >= 25:
        return {
            "offer_kind": "website",
            "recommended_package_id": "business",
            "skip_outreach": False,
            "skip_reason": None,
            "rationale": "Aging / weak site → Website Business redesign",
        }

    # Healthy modern site — do not send template outreach
    issue_count = int(analysis.get("issue_count") or len(analysis.get("issues") or []) or 0)
    imp = int(analysis.get("improvement_score") or 0)
    if score < 15 and issue_count <= 1 and imp < 40:
        return {
            "offer_kind": "skip",
            "recommended_package_id": None,
            "skip_outreach": True,
            "skip_reason": "healthy_site",
            "rationale": "Modern healthy site — skip template outreach",
        }

    return {
        "offer_kind": "website",
        "recommended_package_id": "basic",
        "skip_outreach": False,
        "skip_reason": None,
        "rationale": "Default Path A Basic",
    }


def apply_premium_and_offer(
    row: dict[str, Any],
    *,
    analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Mutate row meta with premium_score + smart offer; return offer dict."""
    analysis = _analysis(row, analysis)
    premium = compute_premium_score(row, analysis=analysis)
    offer = select_smart_offer(row, analysis=analysis, premium=premium)
    meta = dict(row.get("meta") or {})
    meta["premium_score"] = premium["premium_score"]
    meta["premium_breakdown"] = premium.get("breakdown") or {}
    meta["offer_kind"] = offer["offer_kind"]
    meta["smart_offer_rationale"] = offer.get("rationale")
    if offer.get("skip_outreach"):
        meta["skip_reason"] = offer.get("skip_reason") or "healthy_site"
        meta["skip_outreach"] = True
    else:
        meta.pop("skip_reason", None)
        meta["skip_outreach"] = False
        pkg = offer.get("recommended_package_id")
        if pkg:
            row["recommended_package_id"] = pkg
            meta["recommended_package_id"] = pkg
    row["meta"] = meta
    return offer
