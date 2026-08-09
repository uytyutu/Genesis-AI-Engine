"""Score categories from signals — honest 0–100, never invents unavailable data."""

from __future__ import annotations

from typing import Any

from app.integration.vc_auditor.branding import (
    BUSINESS_KEYS,
    LEGAL_DE_KEYS,
    WEBSITE_SCORE_KEYS,
)
from app.integration.vector.capabilities import action_for, is_live


def _clamp(n: int) -> int:
    return max(0, min(100, int(n)))


def score_website(signals: dict[str, Any]) -> dict[str, int]:
    seo = 40
    if signals.get("title"):
        seo += 20
    if signals.get("description"):
        seo += 20
    if int(signals.get("h1_count") or 0) == 1:
        seo += 10
    elif int(signals.get("h1_count") or 0) > 1:
        seo += 5
    if signals.get("open_graph"):
        seo += 5
    if signals.get("canonical"):
        seo += 5
    if int(signals.get("missing_alt") or 0) == 0 and int(signals.get("img_count") or 0) > 0:
        seo += 5
    elif int(signals.get("missing_alt") or 0) > 0:
        seo -= min(15, int(signals["missing_alt"]) * 3)

    perf = 70
    if signals.get("lazy_loading"):
        perf += 15
    elif int(signals.get("img_count") or 0) > 0:
        perf -= 15
    if signals.get("heavy_fonts"):
        perf -= 10
    if int(signals.get("script_count") or 0) > 12:
        perf -= 10
    if signals.get("large_html"):
        perf -= 15
    if int(signals.get("html_bytes") or 0) > 800_000:
        perf -= 10

    a11y = 50
    if signals.get("lang_attr"):
        a11y += 15
    if signals.get("viewport"):
        a11y += 10
    if int(signals.get("missing_alt") or 0) == 0:
        a11y += 15
    else:
        a11y -= min(20, int(signals.get("missing_alt") or 0) * 4)
    if signals.get("aria"):
        a11y += 5
    if signals.get("skip_link"):
        a11y += 5

    mobile = 100 if signals.get("viewport") else 35

    security = 55
    if signals.get("https"):
        security += 35
    else:
        security -= 25
    # Basic: no mixed-content detection without full crawl
    if signals.get("https") and not signals.get("forms"):
        security += 5

    return {
        "seo": _clamp(seo),
        "performance": _clamp(perf),
        "accessibility": _clamp(a11y),
        "mobile": _clamp(mobile),
        "security": _clamp(security),
    }


def score_legal_de(signals: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for key in LEGAL_DE_KEYS:
        ok = bool(signals.get(key))
        out[key] = {
            "id": key,
            "label": {
                "impressum": "Impressum",
                "datenschutz": "Datenschutz",
                "cookie": "Cookie Banner",
                "kontakt": "Kontakt",
            }[key],
            "pass": ok,
            "score": 100 if ok else 0,
        }
    return out


def score_business(signals: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping = {
        "cta": ("Call To Action", "cta"),
        "forms": ("Forms", "forms"),
        "maps": ("Maps", "maps"),
        "social": ("Social", "social"),
        "trust": ("Trust", "trust"),
        "reviews": ("Reviews", "reviews"),
    }
    out: dict[str, dict[str, Any]] = {}
    for key in BUSINESS_KEYS:
        label, sig = mapping[key]
        ok = bool(signals.get(sig))
        out[key] = {
            "id": key,
            "label": label,
            "pass": ok,
            "score": 100 if ok else 0,
        }
    return out


def overall_business_score(
    website: dict[str, int],
    legal: dict[str, dict[str, Any]],
    business: dict[str, dict[str, Any]],
) -> int:
    w_vals = [website[k] for k in WEBSITE_SCORE_KEYS]
    w_avg = sum(w_vals) / len(w_vals)
    legal_avg = sum(int(v["score"]) for v in legal.values()) / max(1, len(legal))
    biz_avg = sum(int(v["score"]) for v in business.values()) / max(1, len(business))
    # Weighted: website 50%, legal 25%, business 25%
    return _clamp(int(round(w_avg * 0.5 + legal_avg * 0.25 + biz_avg * 0.25)))


def build_findings(
    signals: dict[str, Any],
    *,
    virtus_mode: bool,
    locale: str = "de",
) -> list[dict[str, Any]]:
    """Actionable findings — Fix when live, Coming R3.x otherwise (Virtus mode)."""
    de = (locale or "de").lower().startswith("de")
    findings: list[dict[str, Any]] = []

    def add(
        *,
        id: str,
        category: str,
        severity: str,
        message_de: str,
        message_en: str,
        capability: str | None = None,
        fix_label_de: str | None = None,
        fix_label_en: str | None = None,
    ) -> None:
        msg = message_de if de else message_en
        row: dict[str, Any] = {
            "id": id,
            "category": category,
            "severity": severity,
            "message": msg,
            "pass": False,
        }
        if virtus_mode and capability:
            fix = fix_label_de if de else fix_label_en
            if is_live(capability):
                row["action"] = action_for(capability, cta_override=fix or "Fix")
            else:
                row["action"] = action_for(capability)
                if fix:
                    row["action"]["hint_label"] = fix
        elif not virtus_mode:
            row["action"] = {
                "id": "public_cta",
                "kind": "navigate_href",
                "href": "/order",
                "label": "Website mit Virtus Core verbessern" if de else "Improve with Virtus Core",
                "status": "live",
            }
        findings.append(row)

    if not signals.get("impressum"):
        add(
            id="legal_impressum",
            category="legal",
            severity="high",
            message_de="Impressum fehlt",
            message_en="Impressum is missing",
            capability="website_impressum",
            fix_label_de="Impressum erstellen",
            fix_label_en="Create Impressum",
        )
    if not signals.get("datenschutz"):
        add(
            id="legal_datenschutz",
            category="legal",
            severity="high",
            message_de="Datenschutz fehlt",
            message_en="Privacy policy is missing",
            capability="website_impressum",
            fix_label_de="Datenschutz erstellen",
            fix_label_en="Create privacy page",
        )
    if not signals.get("cookie"):
        add(
            id="legal_cookie",
            category="legal",
            severity="medium",
            message_de="Cookie Banner fehlt",
            message_en="Cookie banner is missing",
            capability="website_impressum",
            fix_label_de="Cookie-Hinweis hinzufügen",
            fix_label_en="Add cookie notice",
        )
    if not signals.get("description"):
        add(
            id="seo_description",
            category="seo",
            severity="high",
            message_de="Meta Description fehlt",
            message_en="Meta description is missing",
            capability="website_meta",
            fix_label_de="Beschreibung generieren",
            fix_label_en="Generate description",
        )
    if not signals.get("title"):
        add(
            id="seo_title",
            category="seo",
            severity="high",
            message_de="Meta Title fehlt",
            message_en="Page title is missing",
            capability="website_meta",
            fix_label_de="Title generieren",
            fix_label_en="Generate title",
        )
    if int(signals.get("h1_count") or 0) == 0:
        add(
            id="seo_h1",
            category="seo",
            severity="medium",
            message_de="Kein H1 auf der Seite",
            message_en="No H1 heading found",
            capability="website_meta",
            fix_label_de="H1 hinzufügen",
            fix_label_en="Add H1",
        )
    if int(signals.get("missing_alt") or 0) > 0:
        add(
            id="seo_alt",
            category="seo",
            severity="medium",
            message_de=f"{signals['missing_alt']} Bild(er) ohne Alt-Text",
            message_en=f"{signals['missing_alt']} image(s) missing alt text",
            capability="website_meta",
            fix_label_de="Alt-Texte setzen",
            fix_label_en="Fix image alt",
        )
    if not signals.get("open_graph"):
        add(
            id="seo_og",
            category="seo",
            severity="low",
            message_de="Open Graph Tags fehlen",
            message_en="Open Graph tags are missing",
            capability="website_meta",
            fix_label_de="Open Graph hinzufügen",
            fix_label_en="Add Open Graph",
        )
    if not signals.get("viewport"):
        add(
            id="mobile_viewport",
            category="mobile",
            severity="high",
            message_de="Mobile Viewport Meta fehlt",
            message_en="Mobile viewport meta is missing",
            capability="website_meta",
            fix_label_de="Viewport setzen",
            fix_label_en="Add viewport",
        )
    if not signals.get("https"):
        add(
            id="security_https",
            category="security",
            severity="high",
            message_de="Keine HTTPS-Verbindung",
            message_en="Site is not served over HTTPS",
            capability="website_meta",
            fix_label_de="HTTPS prüfen",
            fix_label_en="Enable HTTPS",
        )
    if int(signals.get("img_count") or 0) > 0 and not signals.get("lazy_loading"):
        add(
            id="perf_lazy",
            category="performance",
            severity="medium",
            message_de="Kein Lazy Loading bei Bildern",
            message_en="Images are not lazy-loaded",
            capability="website_meta",
            fix_label_de="Lazy Loading aktivieren",
            fix_label_en="Enable lazy loading",
        )
    if signals.get("heavy_fonts"):
        add(
            id="perf_fonts",
            category="performance",
            severity="low",
            message_de="Externe Fonts können die Ladezeit verlangsamen",
            message_en="External fonts may slow the page",
            capability="website_meta",
            fix_label_de="Fonts optimieren",
            fix_label_en="Optimize fonts",
        )
    if not signals.get("forms"):
        add(
            id="biz_forms",
            category="business",
            severity="high",
            message_de="Keine Kontaktformular gefunden",
            message_en="No contact form found",
            capability="website_maps",
            fix_label_de="Formular hinzufügen",
            fix_label_en="Add contact form",
        )
    if not signals.get("cta"):
        add(
            id="biz_cta",
            category="business",
            severity="medium",
            message_de="Schwaches oder fehlendes Call-to-Action",
            message_en="Weak or missing call to action",
            capability="website_meta",
            fix_label_de="CTA stärken",
            fix_label_en="Strengthen CTA",
        )
    if not signals.get("maps"):
        add(
            id="biz_maps",
            category="business",
            severity="low",
            message_de="Google Maps / Karte fehlt",
            message_en="Map embed is missing",
            capability="website_maps",
            fix_label_de="Karte hinzufügen",
            fix_label_en="Add Google Maps",
        )
    if not signals.get("social"):
        add(
            id="biz_social",
            category="business",
            severity="low",
            message_de="Keine Social-Media-Links erkannt",
            message_en="No social media links detected",
            capability="website_meta",
            fix_label_de="Social Links hinzufügen",
            fix_label_en="Add social links",
        )
    if int(signals.get("text_len") or 0) < 800:
        add(
            id="content_thin",
            category="content",
            severity="medium",
            message_de="Zu wenig Text für lokales SEO",
            message_en="Too little text for local SEO",
            capability="website_meta",
            fix_label_de="Inhalt erweitern",
            fix_label_en="Expand content",
        )

    return findings
