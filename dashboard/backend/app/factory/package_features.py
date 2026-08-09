"""Path A package → Factory landing feature matrix (honest delivery).

Client-facing commerce: Standalone | Connected (see commerce_model.py).
Legacy basic/business/premium normalize to those modes.
Both modes get full digital-company quality — Connected adds ecosystem hooks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from urllib.parse import quote_plus

from app.factory.analyzer import AnalysisResult


@dataclass(frozen=True)
class PackageFeatures:
    """What the HTML landing must include for a paid package."""

    package_id: str
    whatsapp: bool = True
    maps: bool = False
    testimonials: bool = False
    logo_slot: bool = False
    extended_seo: bool = False
    analytics: bool = False
    calculator: bool = False
    premium_design: bool = False
    contact_form: bool = True
    # Tier design-system blocks
    faq: bool = False
    process: bool = False
    mid_cta: bool = False
    trust_bar: bool = False
    stats_strip: bool = False
    showcase: bool = False
    # Catalog Engine (shop niches only — applied when CatalogView exists)
    catalog_grid: bool = False
    catalog_categories: bool = False
    catalog_search_filter: bool = False
    catalog_request_cart: bool = False
    catalog_rich_cards: bool = False
    # Ecosystem (Connected only)
    ecosystem_connected: bool = False


def _full_digital_company(*, package_id: str, connected: bool) -> PackageFeatures:
    """Full studio-grade product — Standalone and Connected share this floor."""
    return PackageFeatures(
        package_id=package_id,
        maps=True,
        testimonials=True,
        logo_slot=True,
        extended_seo=True,
        analytics=True,
        calculator=True,
        premium_design=True,
        faq=True,
        process=True,
        mid_cta=True,
        trust_bar=True,
        stats_strip=True,
        showcase=True,
        ecosystem_connected=connected,
    )


def resolve_package_features(package_id: str | None) -> PackageFeatures:
    from app.factory.commerce_model import normalize_commerce_mode

    resolved = normalize_commerce_mode(package_id)
    # HTML / CSS still keyed on basic|business|premium — keep data-tier honest for demos.
    legacy = (resolved.legacy_alias or "").strip().lower()
    if legacy in ("basic", "business", "premium"):
        html_tier = legacy
    elif resolved.commerce_mode == "connected":
        html_tier = "premium"
    else:
        html_tier = "business"
    return _full_digital_company(
        package_id=html_tier,
        connected=resolved.ecosystem,
    )


def apply_order_contacts(
    analysis: AnalysisResult,
    *,
    business_name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
) -> AnalysisResult:
    """Prefer real order contacts over analyzer placeholders."""
    name = (business_name or "").strip() or analysis.business_name
    ph = (phone or "").strip() or analysis.phone
    em = (email or "").strip() or analysis.email
    updates: dict = {"business_name": name, "phone": ph, "email": em}
    if name and name != analysis.business_name and " — " in (analysis.headline or ""):
        _, rest = analysis.headline.split(" — ", 1)
        updates["headline"] = f"{name} — {rest}"
    if name and name != analysis.business_name and analysis.about_text:
        updates["about_text"] = analysis.about_text.replace(analysis.business_name, name, 1)
    return replace(analysis, **updates)


def normalize_services_list(raw: object) -> list[str]:
    """Client questionnaire services → clean titles for Factory."""
    items: list[str] = []
    if isinstance(raw, list):
        items = [str(x).strip() for x in raw]
    elif isinstance(raw, str):
        text = raw.replace(";", "\n").replace("|", "\n")
        items = [ln.strip(" •-\t") for ln in text.splitlines()]
    out: list[str] = []
    for item in items:
        if not item or len(item) > 80:
            continue
        if item not in out:
            out.append(item)
        if len(out) >= 8:
            break
    return out


def apply_order_services(
    analysis: AnalysisResult,
    services: object = None,
) -> AnalysisResult:
    """Override analyzer service titles with the client's questionnaire list."""
    cleaned = normalize_services_list(services)
    if len(cleaned) < 2:
        return analysis
    prev_desc = list(analysis.service_descriptions or ())
    descriptions: list[str] = []
    for i, title in enumerate(cleaned):
        if i < len(prev_desc) and str(prev_desc[i]).strip():
            descriptions.append(str(prev_desc[i]).strip())
        else:
            descriptions.append(f"{title} — Details auf Anfrage.")
    updates: dict = {
        "services": cleaned,
        "service_descriptions": tuple(descriptions),
    }
    # If hero still used a banned partner phrase, retitle from first service.
    hl = (analysis.headline or "").lower()
    if "partner vor ort" in hl or "helfen ihrem" in hl:
        name = analysis.business_name
        updates["headline"] = f"{name} — {cleaned[0]}"
        updates["subtitle"] = " · ".join(cleaned[:3])
    return replace(analysis, **updates)


def apply_order_advantages(
    analysis: AnalysisResult,
    advantages: object = None,
) -> AnalysisResult:
    """Map client advantages into benefits when at least two are provided."""
    items = normalize_services_list(advantages)
    if len(items) < 2:
        return analysis
    return replace(analysis, benefits=tuple(items[:4]))


def normalize_whatsapp_digits(raw: str) -> str:
    digits = re.sub(r"\D", "", (raw or "").strip())
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0") and len(digits) >= 10:
        digits = "49" + digits[1:]
    return digits


def whatsapp_href(whatsapp: str, phone_fallback: str = "") -> str:
    digits = normalize_whatsapp_digits(whatsapp) or normalize_whatsapp_digits(phone_fallback)
    if not digits:
        return "#contact"
    return f"https://wa.me/{digits}"


def maps_embed_src(
    *,
    business_name: str,
    city: str,
    street: str = "",
    country: str = "Germany",
) -> str:
    """Map iframe src — Nominatim/OSM when GENESIS_CAP_NOMINATIM=1, else Google embed."""
    try:
        from app.integration.external_capabilities import resolve_maps_embed

        result = resolve_maps_embed(
            business_name=business_name,
            city=city,
            street=street,
            country=country,
        )
        url = (result.data or {}).get("embed_url")
        if url:
            return str(url)
    except Exception:
        pass
    query = " ".join(p for p in (business_name, street, city, country) if p).strip()
    return f"https://maps.google.com/maps?q={quote_plus(query)}&z=14&output=embed"


def maps_route_url(
    *,
    business_name: str,
    city: str,
    street: str = "",
    country: str = "Germany",
) -> str:
    """Google Maps directions deep-link for Business+ route CTA."""
    dest = " ".join(p for p in (street, city, country, business_name) if p).strip()
    if not dest:
        return "#maps"
    return f"https://www.google.com/maps/dir/?api=1&destination={quote_plus(dest)}"


def delivery_meta(features: PackageFeatures) -> dict:
    return {
        "package_id": features.package_id,
        "whatsapp": features.whatsapp,
        "maps": features.maps,
        "testimonials": features.testimonials,
        "logo_slot": features.logo_slot,
        "extended_seo": features.extended_seo,
        "analytics": features.analytics,
        "calculator": features.calculator,
        "premium_design": features.premium_design,
        "contact_form": features.contact_form,
        "faq": features.faq,
        "process": features.process,
        "mid_cta": features.mid_cta,
        "trust_bar": features.trust_bar,
        "stats_strip": features.stats_strip,
        "showcase": features.showcase,
        "catalog_grid": features.catalog_grid,
        "catalog_categories": features.catalog_categories,
        "catalog_search_filter": features.catalog_search_filter,
        "catalog_request_cart": features.catalog_request_cart,
        "catalog_rich_cards": features.catalog_rich_cards,
        "ecosystem_connected": features.ecosystem_connected,
    }

def maps_embed_url(
    *,
    business_name: str,
    street: str = "",
    city: str = "",
    country: str = "Deutschland",
) -> str:
    """Alias for callers using the newer name; prefers street-first query order."""
    return maps_embed_src(
        business_name=business_name,
        city=city,
        street=street,
        country=country or "Germany",
    )


def maps_directions_url(
    *,
    business_name: str,
    street: str = "",
    city: str = "",
    country: str = "Deutschland",
) -> str:
    """Alias for maps_route_url with street-first argument style."""
    return maps_route_url(
        business_name=business_name,
        city=city,
        street=street,
        country=country or "Germany",
    )


def features_as_dict(features: PackageFeatures) -> dict:
    return delivery_meta(features)


__all__ = [
    "PackageFeatures",
    "apply_order_advantages",
    "apply_order_contacts",
    "apply_order_services",
    "delivery_meta",
    "features_as_dict",
    "maps_directions_url",
    "maps_embed_src",
    "maps_embed_url",
    "maps_route_url",
    "normalize_services_list",
    "normalize_whatsapp_digits",
    "resolve_package_features",
    "whatsapp_href",
]
