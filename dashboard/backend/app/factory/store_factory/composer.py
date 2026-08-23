"""Compose static HTML pages from shop_brief + resolved template (AI Store R2.1)."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from app.factory.store_factory.design_bridge import (
    emit_store_root_css,
    ensure_image_slot_dirs,
    font_link_tags,
    niche_store_css,
    resolve_store_design,
    visual_preset_for_niche,
)
from app.factory.store_factory.templates import ResolvedTemplate

# brief.pages id → filename(s)
_PAGE_FILES: dict[str, tuple[str, ...]] = {
    "home": ("index.html",),
    "catalog": ("catalog.html",),
    "pdp": ("product.html",),
    "about": ("about.html",),
    "contact": ("contact.html",),
    "faq": ("faq.html",),
    "legal": ("impressum.html", "datenschutz.html"),
    "returns": ("returns.html",),
    "news": ("news.html",),
    "blog": ("blog.html",),
    "cart": ("cart.html",),
}


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", str(text or "").strip().lower()).strip("-")
    return s or "store"


def _is_dach(brief: dict[str, Any]) -> bool:
    market = str(brief.get("market_code") or brief.get("country") or "").upper()
    langs = brief.get("languages") if isinstance(brief.get("languages"), list) else []
    lang0 = str(langs[0]).lower() if langs else ""
    return market in ("DE", "AT", "CH") or lang0.startswith("de")


def _niche_brand_story(category: str, what_is_sold: str) -> tuple[str, str, str, str, str]:
    """Law №3: store story sells the future company — not generic ritual copy."""
    cat = (category or "").strip().lower()
    what = (what_is_sold or "").strip()
    stories: dict[str, tuple[str, str, str, str, str]] = {
        "dachreinigung": (
            "Warum DachKlar Shop",
            "Werkzeug und Pflegeprodukte für echte Dach- und Fassadenarbeit — "
            "kein Lifestyle-Katalog. Was Profis auf dem Dach brauchen.",
            "Reinigung",
            "Schutz",
            "Sicherheit",
        ),
        "psychology": (
            "Warum Klarheit Digital",
            "Digitale Begleitung für ruhige Schritte: Kurse, Audio und Materialien — "
            "ehrlich, vertraulich, ohne Wellness-Floskeln.",
            "Beratung",
            "Kurse",
            "Materialien",
        ),
        "food": (
            "Warum FeinKost",
            "Regionale Spezialitäten und Feinkost mit klarer Herkunft — "
            "Geschmack, der zur Küche und zum Tisch passt.",
            "Pantry",
            "Frisch",
            "Geschenke",
        ),
        "beauty": (
            "Warum Glow Lab",
            "Hautpflege und Rituale mit ehrlichen Inhaltsstoffen — "
            "für den Alltag, nicht für die Vitrine.",
            "Pflege",
            "Sets",
            "SPF",
        ),
        "clothing": (
            "Warum Nordlicht",
            "Mode für den deutschen Alltag — klare Schnitte, ehrliche Stoffe, "
            "kein Saison-Lärm.",
            "Neu",
            "Basics",
            "Accessoires",
        ),
        "handwerk": (
            "Warum Werkstatt Direkt",
            "Material und Werkzeug für Handwerker, die sauber und pünktlich arbeiten.",
            "Werkzeug",
            "Material",
            "Kits",
        ),
    }
    if cat in stories:
        return stories[cat]
    body = (
        f"{what} — kuratiert für echte Kunden, nicht als generischer Katalog."
        if what
        else "Ehrlich kuratiert für echte Kunden — nicht als generischer Katalog."
    )
    return ("Unsere Geschichte", body, "Auswahl", "Bestsellers", "Essentials")


def ui_copy(brief: dict[str, Any]) -> dict[str, str]:
    """Storefront chrome strings — DE-first for DACH, else English."""
    category = str(brief.get("category") or "other").strip().lower()
    what = str(brief.get("what_is_sold") or "")
    story_title, story_body, col1, col2, col3 = _niche_brand_story(category, what)
    if _is_dach(brief):
        return {
            "lang": "de",
            "home": "Startseite",
            "catalog": "Katalog",
            "cart": "Warenkorb",
            "about": "Über uns",
            "contact": "Kontakt",
            "faq": "FAQ",
            "privacy": "Datenschutz",
            "returns": "Rückgabe",
            "news": "News",
            "blog": "Blog",
            "deals": "Angebote",
            "wishlist": "Merkliste",
            "account": "Kundenkonto",
            "account_title": "Mein Kundenkonto",
            "login": "Anmelden",
            "register": "Registrieren",
            "nav_shop": "Shop",
            "nav_account": "Konto",
            "nav_info": "Info",
            "nav_legal": "Rechtliches",
            "search_ph": "Produkte suchen…",
            "menu_open": "Menü öffnen",
            "menu_close": "Menü schließen",
            "add_cart": "In den Warenkorb",
            "buy_now": "Jetzt kaufen",
            "categories": "Kategorien",
            "featured": "Empfohlen",
            "new_arrivals": "Neuheiten",
            "bestsellers": "Bestseller",
            "reviews": "Kundenstimmen",
            "why_us": "Warum bei uns kaufen",
            "secure_pay": "Sichere Zahlung",
            "shipping": "Versand",
            "niche": "Fokus",
            "care": "Kundenservice",
            "care_detail": "Rechtliche Seiten für DE inklusive",
            "newsletter": "Bleiben Sie informiert",
            "newsletter_body": "Neuheiten und saisonale Angebote — kein Spam.",
            "email_ph": "E-Mail-Adresse",
            "subscribe": "Abonnieren",
            "shop": "Shop",
            "service": "Service",
            "pay_ship": "Zahlung & Versand",
            "powered": "Premium-Shop von Virtus Core",
            "cart_title": "Warenkorb",
            "cart_hint": "Merkliste & Warenkorb werden in diesem Browser gespeichert (Demo).",
            "cart_empty": "Ihr Warenkorb ist leer.",
            "wish_empty": "Ihre Merkliste ist leer.",
            "wish_title": "Merkliste",
            "browse": "Zum Katalog",
            "order_summary": "Bestellübersicht",
            "promo": "Gutscheincode",
            "promo_optional": "Optional",
            "apply": "Einlösen",
            "total": "Summe",
            "checkout": "Zur Kasse",
            "checkout_note": (
                "Checkout 1.0 — Bestellung wird gespeichert. "
                "Live-Kartenzahlung folgt mit Stripe OAuth."
            ),
            "checkout_title": "Kasse",
            "toast_added": "Zum Warenkorb hinzugefügt",
            "toast_wish_add": "Auf die Merkliste",
            "toast_wish_rm": "Von der Merkliste entfernt",
            "toast_checkout": "Weiter zur Kasse…",
            "toast_promo": "Gutscheine folgen später",
            "remove": "Entfernen",
            "in_stock": "Auf Lager",
            "few_left": "Nur noch wenige",
            "related": "Das könnte Ihnen auch gefallen",
            "reviews_count": "Bewertungen",
            "hero_suffix": "Kuratiert für {category} — modernes Einkaufen mit Premium-Gefühl.",
            "hero_why": "Warum hier kaufen",
            "hero_benefit_1": "Kostenloser Versand ab 49 €",
            "hero_benefit_2": "14 Tage Rückgabe",
            "hero_benefit_3": "Sichere Zahlung (Stripe)",
            "hero_benefit_4": "Geprüfte Qualität",
            "brand_story_title": story_title,
            "brand_story_body": story_body,
            "collections_title": "Kollektionen",
            "collection_1": col1,
            "collection_2": col2,
            "collection_3": col3,
            "cta_catalog": "Zum Katalog",
            "cta_buy": "Jetzt kaufen",
            "trust_delivery": "Schnelle Lieferung",
            "trust_delivery_detail": "DHL · Tracking inklusive",
            "trust_returns": "Einfache Rückgabe",
            "trust_returns_detail": "14 Tage · unkompliziert",
            "trust_pay": "Sichere Zahlung",
            "trust_pay_detail": "Stripe · SSL",
            "trust_guarantee": "Zufriedenheitsgarantie",
            "trust_guarantee_detail": "Qualität, die hält",
            "trust_contact": "Direkter Kontakt",
            "trust_contact_detail": "Support in Deutsch",
            "badge_new": "NEU",
            "badge_sale": "SALE",
            "badge_hit": "HIT",
            "description": "Beschreibung",
            "specs_title": "Eigenschaften",
            "variants": "Variante",
            "size": "Größe",
            "color": "Farbe",
            "recent": "Zuletzt angesehen",
            "zoom_hint": "Tippen zum Vergrößern",
            "filter_all": "Alle",
            "review_1_name": "Anna M.",
            "review_1_text": "Schnelle Lieferung und tolle Qualität — genau wie beschrieben.",
            "review_2_name": "Thomas K.",
            "review_2_text": "Der Shop wirkt professionell. Einfach zu bestellen.",
            "review_3_name": "Lisa B.",
            "review_3_text": "Schönes Design und guter Service. Gerne wieder.",
        }
    return {
        "lang": "en",
        "home": "Home",
        "catalog": "Catalog",
        "cart": "Cart",
        "about": "About",
        "contact": "Contact",
        "faq": "FAQ",
        "privacy": "Privacy",
        "returns": "Returns",
        "news": "News",
        "blog": "Blog",
        "deals": "Deals",
        "wishlist": "Wishlist",
        "account": "My account",
        "account_title": "My account",
        "login": "Sign in",
        "register": "Register",
        "nav_shop": "Shop",
        "nav_account": "Account",
        "nav_info": "Info",
        "nav_legal": "Legal",
        "search_ph": "Search products…",
        "menu_open": "Open menu",
        "menu_close": "Close menu",
        "add_cart": "Add to Cart",
        "buy_now": "Buy Now",
        "categories": "Categories",
        "featured": "Featured",
        "new_arrivals": "New arrivals",
        "bestsellers": "Bestsellers",
        "reviews": "Customer reviews",
        "why_us": "Why shop with us",
        "secure_pay": "Secure payments",
        "shipping": "Shipping",
        "niche": "Niche focus",
        "care": "Customer care",
        "care_detail": "DE-ready legal pages included",
        "newsletter": "Stay in the loop",
        "newsletter_body": "New arrivals and seasonal offers — no spam.",
        "email_ph": "Email address",
        "subscribe": "Subscribe",
        "shop": "Shop",
        "service": "Service",
        "pay_ship": "Payments & shipping",
        "powered": "Premium storefront by Virtus Core",
        "cart_title": "Shopping cart",
        "cart_hint": "Wishlist & cart are saved in this browser (demo).",
        "cart_empty": "Your cart is empty.",
        "wish_empty": "Your wishlist is empty.",
        "wish_title": "Wishlist",
        "browse": "Browse catalog",
        "order_summary": "Order summary",
        "promo": "Promo code",
        "promo_optional": "Optional",
        "apply": "Apply",
        "total": "Total",
        "checkout": "Checkout",
        "checkout_note": (
            "Checkout 1.0 — order is stored. Live card charge comes with Stripe OAuth."
        ),
        "checkout_title": "Checkout",
        "toast_added": "Added to cart",
        "toast_wish_add": "Saved to wishlist",
        "toast_wish_rm": "Removed from wishlist",
        "toast_checkout": "Continuing to checkout…",
        "toast_promo": "Promo codes come later",
        "remove": "Remove",
        "in_stock": "In stock",
        "few_left": "Few left",
        "related": "You may also like",
        "reviews_count": "reviews",
        "hero_suffix": "Curated for {category} — crafted for everyday premium shopping.",
        "hero_why": "Why shop here",
        "hero_benefit_1": "Free shipping from €49",
        "hero_benefit_2": "14-day returns",
        "hero_benefit_3": "Secure checkout (Stripe)",
        "hero_benefit_4": "Quality checked",
        "brand_story_title": story_title if story_title != "Unsere Geschichte" else "Our story",
        "brand_story_body": story_body,
        "collections_title": "Collections",
        "collection_1": col1,
        "collection_2": col2,
        "collection_3": col3,
        "cta_catalog": "Browse catalog",
        "cta_buy": "Buy now",
        "trust_delivery": "Fast delivery",
        "trust_delivery_detail": "Tracked shipping",
        "trust_returns": "Easy returns",
        "trust_returns_detail": "14 days · hassle-free",
        "trust_pay": "Secure payment",
        "trust_pay_detail": "Stripe · SSL",
        "trust_guarantee": "Satisfaction guarantee",
        "trust_guarantee_detail": "Quality that lasts",
        "trust_contact": "Direct contact",
        "trust_contact_detail": "Real support",
        "badge_new": "NEW",
        "badge_sale": "SALE",
        "badge_hit": "HIT",
        "description": "Description",
        "specs_title": "Specifications",
        "variants": "Variant",
        "size": "Size",
        "color": "Color",
        "recent": "Recently viewed",
        "zoom_hint": "Tap to zoom",
        "filter_all": "All",
        "review_1_name": "Anna M.",
        "review_1_text": "Fast shipping and great quality — exactly as described.",
        "review_2_name": "Thomas K.",
        "review_2_text": "The store feels professional. Easy to order.",
        "review_3_name": "Lisa B.",
        "review_3_text": "Beautiful design and solid service. Will buy again.",
    }


def pages_for_brief(brief: dict[str, Any]) -> list[str]:
    requested = brief.get("pages") if isinstance(brief.get("pages"), list) else []
    ids = [str(x).strip().lower() for x in requested if str(x).strip()]
    if "home" not in ids:
        ids = ["home", *ids]
    if "catalog" not in ids:
        ids.append("catalog")
    if "cart" not in ids:
        ids.append("cart")
    market = str(brief.get("market_code") or brief.get("country") or "").upper()
    if "legal" not in ids and market in ("", "DE", "AT", "CH"):
        ids.append("legal")
    if "contact" not in ids:
        ids.append("contact")
    files: list[str] = []
    seen: set[str] = set()
    for pid in ids:
        for name in _PAGE_FILES.get(pid, ()):
            if name not in seen:
                seen.add(name)
                files.append(name)
    return files


def _store_tier_perception_css(package_id: str, niche_id: str) -> str:
    """Ladder CSS so Basic / Business / Premium stores feel like different products."""
    pid = (package_id or "business").strip().lower() or "business"
    niche = (niche_id or "generic").strip().lower()
    if pid == "basic":
        return """
/* Store ladder — Starter */
body[data-tier="basic"] .hero.has-hero-image { min-height: min(62vh, 640px); }
body[data-tier="basic"] .card {
  box-shadow: 0 6px 18px rgba(28,25,23,0.06); border-radius: 12px;
}
body[data-tier="basic"] .card:hover { transform: none; }
body[data-tier="basic"] .promo-banner { min-height: 10rem; }
"""
    if pid == "business":
        return """
/* Store ladder — Business */
body[data-tier="business"] .hero.has-hero-image { min-height: min(74vh, 780px); }
body[data-tier="business"] .card {
  box-shadow: 0 14px 36px rgba(28,25,23,0.10); border-radius: 16px;
}
body[data-tier="business"] .card:hover {
  transform: translateY(-4px); box-shadow: 0 22px 48px rgba(28,25,23,0.14);
}
body[data-tier="business"] .section-band {
  background: color-mix(in srgb, var(--store-secondary) 55%, var(--store-bg));
  padding: 3.5rem 0;
}
"""
    psych = ""
    if niche == "psychology":
        psych = """
/* Psychology store — Virtus-grade sage atmosphere (not white paper) */
body[data-niche="psychology"] {
  --store-header-glass: color-mix(in srgb, var(--store-surface) 78%, transparent);
}
body[data-niche="psychology"] .site-header {
  background: var(--store-header-glass);
  border-bottom-color: color-mix(in srgb, var(--store-accent) 22%, transparent);
  box-shadow: 0 1px 0 rgba(255,255,255,0.04);
}
body[data-niche="psychology"] .search-input,
body[data-niche="psychology"] .card,
body[data-niche="psychology"] .product-card--premium {
  background: color-mix(in srgb, var(--store-surface) 92%, var(--store-primary));
  border-color: color-mix(in srgb, var(--store-accent) 18%, transparent);
  color: var(--store-text);
}
body[data-niche="psychology"] .section-alt {
  background: color-mix(in srgb, var(--store-secondary) 55%, var(--store-bg));
}
body[data-tier="premium"][data-niche="psychology"] .card {
  border-radius: 20px;
  background: rgba(28,36,32,0.88);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(201,184,166,0.18);
  box-shadow: 0 22px 50px rgba(0,0,0,0.28);
}
body[data-tier="premium"][data-niche="psychology"] .badge,
body[data-tier="premium"][data-niche="psychology"] .card .badge {
  opacity: 0.72; letter-spacing: 0.06em; font-size: 0.65rem;
}
body[data-tier="premium"][data-niche="psychology"] .offer-glass {
  background: rgba(20,26,23,0.72);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(201,184,166,0.28);
  border-radius: 1.25rem;
  padding: 1.5rem;
}
body[data-tier="premium"][data-niche="psychology"] .brand-story p,
body[data-tier="premium"][data-niche="psychology"] .muted {
  color: color-mix(in srgb, var(--store-muted) 90%, #fff);
}
"""
    return f"""
/* Store ladder — Premium */
body[data-tier="premium"] .hero.has-hero-image,
body[data-tier="premium"] .hero.hero-luxury {{
  min-height: min(92vh, 960px);
  align-items: flex-end;
}}
body[data-tier="premium"] .hero.has-hero-image::before {{
  background: linear-gradient(105deg, rgba(8,6,4,0.72) 0%, rgba(8,6,4,0.28) 55%, rgba(8,6,4,0.12) 100%);
}}
body[data-tier="premium"] .hero.hero-luxury h1 {{
  font-size: clamp(2.6rem, 6.5vw, 4.2rem);
  letter-spacing: -0.035em;
  max-width: 12ch;
}}
body[data-tier="premium"] .hero.hero-luxury .btn {{
  background: linear-gradient(135deg, #c5a572, #a78b5a);
  color: #0c0a09;
  border: 0;
  box-shadow: 0 16px 40px rgba(0,0,0,0.28);
}}
body[data-tier="premium"] .card,
body[data-tier="premium"] .product-card--premium {{
  border-radius: 1.15rem;
  box-shadow: 0 22px 56px rgba(15,23,42,0.12);
  transition: transform .35s ease, box-shadow .35s ease;
}}
body[data-tier="premium"] .card:hover,
body[data-tier="premium"] .product-card--premium:hover {{
  transform: translateY(-6px);
  box-shadow: 0 28px 64px rgba(15,23,42,0.16);
}}
body[data-tier="premium"] .promo-banner {{
  min-height: 16rem;
  border-radius: 1.25rem;
  overflow: hidden;
}}
body[data-tier="premium"] .brand-story {{
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 2.5rem;
  align-items: center;
  padding: 4.5rem 0 3rem;
}}
body[data-tier="premium"] .brand-story h2 {{
  font-size: clamp(1.85rem, 3.5vw, 2.6rem);
  letter-spacing: -0.02em;
  max-width: 14ch;
  margin: 0 0 1rem;
}}
body[data-tier="premium"] .brand-story p {{
  font-size: 1.08rem;
  line-height: 1.65;
  max-width: 38ch;
  opacity: 0.88;
}}
body[data-tier="premium"] .brand-story-media {{
  border-radius: 1.5rem;
  overflow: hidden;
  min-height: 18rem;
  box-shadow: 0 28px 70px rgba(15,23,42,0.16);
}}
body[data-tier="premium"] .brand-story-media img {{
  width: 100%; height: 100%; object-fit: cover; display: block; min-height: 18rem;
}}
body[data-tier="premium"] .collections-grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.1rem;
}}
body[data-tier="premium"] .collection-tile {{
  position: relative;
  border-radius: 1.25rem;
  overflow: hidden;
  min-height: 14rem;
  display: flex;
  align-items: flex-end;
  padding: 1.25rem;
  color: #fafaf9;
  text-decoration: none;
  background: #1c1917;
}}
body[data-tier="premium"] .collection-tile img {{
  position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover;
  opacity: 0.72; transition: transform .5s ease, opacity .35s ease;
}}
body[data-tier="premium"] .collection-tile:hover img {{
  transform: scale(1.06); opacity: 0.88;
}}
body[data-tier="premium"] .collection-tile span {{
  position: relative; z-index: 1;
  font-size: 1.15rem; font-weight: 600; letter-spacing: -0.01em;
  text-shadow: 0 2px 16px rgba(0,0,0,0.45);
}}
@media (max-width: 860px) {{
  body[data-tier="premium"] .brand-story {{ grid-template-columns: 1fr; }}
  body[data-tier="premium"] .collections-grid {{ grid-template-columns: 1fr; }}
}}
{psych}
"""


def compose_store_css(resolved: ResolvedTemplate, *, package_id: str = "business") -> str:
    c = resolved.colors
    niche_id = resolved.niche_id or "generic"
    pid = (package_id or "business").strip().lower() or "business"
    cat_for_bridge = {
        "fashion": "clothing",
        "beauty": "beauty",
        "auto": "auto",
        "computer": "electronics",
        "restaurant": "food",
        "handwerk": "handwerk",
        "realestate": "furniture",
        "psychology": "psychology",
        "generic": "other",
    }.get(niche_id, "other")
    tokens, _preset_default, _pack = resolve_store_design(
        cat_for_bridge, package_id=pid
    )
    preset = resolved.visual_preset or visual_preset_for_niche(niche_id)
    root = emit_store_root_css(colors=c, tokens=tokens, preset=preset)
    hero_grad = c.get("hero_gradient") or tokens.hero_gradient
    niche_css = niche_store_css(preset)
    motion_tier = (
        "premium" if pid == "premium" else "business" if pid == "business" else "basic"
    )
    try:
        from app.factory.visual_intelligence.motion_engine import emit_motion_css

        vie_motion = emit_motion_css(motion_tier, surface="store")
    except Exception:
        vie_motion = ""
    tier_css = _store_tier_perception_css(pid, niche_id)
    from app.factory.store_factory.templates import _is_dark_canvas

    dark = _is_dark_canvas(str(c.get("background") or ""))
    # Site-parity depth: always ship deep atmospheric canvas + locked light ink on dark.
    dark_css = ""
    if dark:
        dark_css = """
/* Site-parity atmospheric depth + locked readability */
body[data-canvas="dark"] {
  color: #fafaf9 !important;
  font-weight: 500;
}
body[data-canvas="dark"] .site-header {
  background: rgba(8,10,12,0.72) !important;
  border-bottom-color: rgba(255,255,255,0.1);
  box-shadow: 0 12px 40px rgba(0,0,0,0.35);
}
body[data-canvas="dark"] .brand,
body[data-canvas="dark"] .brand-word,
body[data-canvas="dark"] .icon-btn,
body[data-canvas="dark"] .page-title,
body[data-canvas="dark"] .section h2,
body[data-canvas="dark"] .section h3,
body[data-canvas="dark"] .card,
body[data-canvas="dark"] .card h3,
body[data-canvas="dark"] .card .price,
body[data-canvas="dark"] .card strong,
body[data-canvas="dark"] .review-card p,
body[data-canvas="dark"] .brand-story h2,
body[data-canvas="dark"] .brand-story p,
body[data-canvas="dark"] .nav-drawer,
body[data-canvas="dark"] .nav-drawer a,
body[data-canvas="dark"] .nav-drawer h2,
body[data-canvas="dark"] .header-auth a,
body[data-canvas="dark"] .mobile-bar a,
body[data-canvas="dark"] .cat-chip,
body[data-canvas="dark"] .footer-grid,
body[data-canvas="dark"] .footer-grid a,
body[data-canvas="dark"] .site-footer,
body[data-canvas="dark"] footer {
  color: #fafaf9 !important;
}
body[data-canvas="dark"] .muted,
body[data-canvas="dark"] .card .muted,
body[data-canvas="dark"] .card-meta,
body[data-canvas="dark"] .section p,
body[data-canvas="dark"] .nav-group {
  color: rgba(250,250,249,0.88) !important;
}
body[data-canvas="dark"] .card,
body[data-canvas="dark"] .product-card--premium,
body[data-canvas="dark"] .review-card,
body[data-canvas="dark"] .offer-glass,
body[data-canvas="dark"] .search-input,
body[data-canvas="dark"] #header-search,
body[data-canvas="dark"] form input,
body[data-canvas="dark"] form textarea,
body[data-canvas="dark"] .cart-summary {
  background: rgba(18,22,20,0.82) !important;
  border-color: rgba(255,255,255,0.14) !important;
  color: #fafaf9 !important;
  backdrop-filter: blur(12px);
}
body[data-canvas="dark"] .section-alt,
body[data-canvas="dark"] .section-band {
  background: rgba(255,255,255,0.04) !important;
}
/* Departments / Kategorien — must stay readable on deep canvas */
body[data-canvas="dark"] #categories h2,
body[data-canvas="dark"] #collections h2 {
  color: #fafaf9 !important;
}
body[data-canvas="dark"] .cat-chip,
body[data-canvas="dark"] a.cat-chip {
  background: color-mix(in srgb, var(--store-surface) 88%, #000) !important;
  border: 1px solid color-mix(in srgb, var(--store-accent) 45%, rgba(255,255,255,0.22)) !important;
  color: #fafaf9 !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  letter-spacing: 0.01em;
  box-shadow: 0 10px 28px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08);
  text-decoration: none !important;
}
body[data-canvas="dark"] .cat-chip:hover,
body[data-canvas="dark"] a.cat-chip:hover {
  background: color-mix(in srgb, var(--store-accent) 28%, var(--store-surface)) !important;
  border-color: var(--store-accent) !important;
  color: #fafaf9 !important;
  transform: translateY(-2px);
}
body[data-canvas="dark"] .collection-tile,
body[data-canvas="dark"] a.collection-tile {
  color: #fafaf9 !important;
  background:
    linear-gradient(180deg, transparent 20%, rgba(0,0,0,0.72) 100%),
    color-mix(in srgb, var(--store-surface) 80%, #000) !important;
}
body[data-canvas="dark"] .collection-tile span,
body[data-canvas="dark"] a.collection-tile span {
  color: #fafaf9 !important;
  font-weight: 700 !important;
  font-size: 1.2rem !important;
  text-shadow: 0 2px 18px rgba(0,0,0,0.75) !important;
}
body[data-canvas="dark"] .collection-tile::after {
  content: "";
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.15), rgba(0,0,0,0.65));
  pointer-events: none;
  z-index: 0;
}
body[data-canvas="dark"] .collection-tile span { z-index: 2; }
body[data-canvas="dark"] .hero h1,
body[data-canvas="dark"] .hero .lead,
body[data-canvas="dark"] .hero p {
  color: #fafaf9 !important;
  text-shadow: 0 2px 28px rgba(0,0,0,0.45);
}
body[data-canvas="dark"] .hero.has-hero-image::before {
  background: linear-gradient(105deg, rgba(8,6,4,0.78) 0%, rgba(8,6,4,0.35) 55%, rgba(8,6,4,0.18) 100%) !important;
}
"""
    depth_css = """
/* Deep living canvas — match website atmosphere grade */
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: var(--font-sans);
  color: var(--store-text);
  line-height: 1.65;
  font-weight: 500;
  min-height: 100vh;
  position: relative;
  isolation: isolate;
  background:
    radial-gradient(ellipse 85% 55% at 50% -8%, color-mix(in srgb, var(--store-accent) 34%, transparent), transparent 58%),
    radial-gradient(ellipse 55% 40% at 92% 12%, color-mix(in srgb, var(--store-accent) 22%, transparent), transparent 55%),
    radial-gradient(ellipse 50% 45% at 8% 78%, color-mix(in srgb, var(--store-secondary) 55%, transparent), transparent 55%),
    linear-gradient(165deg, var(--store-bg) 0%, color-mix(in srgb, var(--store-accent) 14%, var(--store-bg)) 42%, var(--store-bg) 100%) !important;
  background-attachment: fixed;
}
body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(circle at 18% 68%, color-mix(in srgb, var(--store-accent) 16%, transparent), transparent 38%),
    radial-gradient(circle at 82% 42%, color-mix(in srgb, var(--store-primary) 12%, transparent), transparent 42%),
    radial-gradient(ellipse 70% 50% at 50% 100%, rgba(0,0,0,0.35), transparent 60%);
  filter: blur(48px);
  opacity: 0.95;
}
body::after {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: 0.18;
  background-image:
    linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: radial-gradient(ellipse 75% 65% at 50% 28%, black, transparent 78%);
}
.wrap, .site-header, .site-footer, .mobile-bar, .nav-drawer { position: relative; z-index: 1; }
.page-title, .section h2 {
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: -0.02em;
}
.card h3, .brand-word { font-weight: 700; }
/* Premium typography visibility — restaurant-site grade */
h1, .hero h1, .page-title {
  font-family: var(--font-display) !important;
  font-weight: 700 !important;
  letter-spacing: -0.03em;
  line-height: 1.08;
}
h2, .section h2, .brand-story h2, .newsletter h2 {
  font-family: var(--font-display) !important;
  font-weight: 650 !important;
  letter-spacing: -0.02em;
}
.hero h1 {
  font-size: clamp(2.35rem, 5.5vw, 3.85rem) !important;
  color: #fafaf9 !important;
  text-shadow: 0 2px 28px rgba(0,0,0,0.45);
}
.hero p, .hero .lead {
  color: rgba(250,250,249,0.9) !important;
  font-weight: 500;
}
body {
  font-family: var(--font-sans) !important;
}
"""
    return f"""/* AI Store — Design Engine + Visual Intelligence · tier={pid} */
{root}
{vie_motion}
{tier_css}
{dark_css}
{depth_css}
:root {{
  --store-hero-gradient: {hero_grad};
  --store-hero-image: url("images/hero.jpg");
  --store-product-image: url("images/product.jpg");
}}

* {{ box-sizing: border-box; }}
a {{ color: var(--store-accent); text-decoration: none; transition: color 0.2s ease; }}
a:hover {{ color: var(--store-primary); }}
.wrap {{ max-width: 1180px; margin: 0 auto; padding: 0 1.25rem; position: relative; z-index: 1; }}

/* Sticky header */
.site-header {{
  position: sticky;
  top: 0;
  z-index: 40;
  backdrop-filter: blur(14px);
  background: color-mix(in srgb, var(--store-surface) 82%, transparent);
  border-bottom: 1px solid color-mix(in srgb, var(--store-secondary) 70%, transparent);
  box-shadow: 0 1px 0 rgba(255,255,255,0.4);
}}
.site-header-inner {{
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.85rem 0;
}}
.icon-btn {{
  appearance: none;
  border: none;
  background: color-mix(in srgb, var(--store-secondary) 55%, transparent);
  color: var(--store-text);
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.75rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
  font-size: 1.1rem;
  position: relative;
}}
.icon-btn:hover {{
  transform: translateY(-1px);
  background: var(--store-secondary);
  box-shadow: var(--store-shadow);
}}
.brand {{
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1.35rem;
  color: var(--store-primary);
  letter-spacing: -0.02em;
  white-space: nowrap;
}}
.brand:hover {{ text-decoration: none; color: var(--store-accent); }}
.header-search {{
  flex: 1;
  min-width: 0;
  display: none;
}}
@media (min-width: 720px) {{
  .header-search {{ display: block; }}
}}
.header-search input {{
  width: 100%;
  max-width: none;
  padding: 0.65rem 1rem;
  border: 1px solid color-mix(in srgb, var(--store-secondary) 90%, var(--store-muted));
  border-radius: 999px;
  background: color-mix(in srgb, var(--store-surface) 90%, #fff);
  font: inherit;
  color: var(--store-text);
}}
.header-search input:focus {{
  outline: 2px solid color-mix(in srgb, var(--store-accent) 45%, transparent);
  border-color: var(--store-accent);
}}
.header-actions {{ display: flex; align-items: center; gap: 0.4rem; margin-left: auto; }}
.cart-badge {{
  position: absolute;
  top: -0.2rem;
  right: -0.2rem;
  min-width: 1.15rem;
  height: 1.15rem;
  padding: 0 0.25rem;
  border-radius: 999px;
  background: var(--store-accent);
  color: #fff;
  font-size: 0.65rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transform: scale(0.9);
  transition: transform 0.25s ease;
}}
.cart-badge.has-items {{ transform: scale(1); }}
.cart-badge[data-count="0"] {{ display: none; }}

/* Drawer */
.drawer-overlay {{
  position: fixed;
  inset: 0;
  background: rgba(28, 25, 23, 0.35);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.25s ease;
  z-index: 50;
}}
.drawer-overlay.open {{ opacity: 1; pointer-events: auto; }}
.nav-drawer {{
  position: fixed;
  top: 0;
  left: 0;
  height: 100%;
  width: min(20rem, 88vw);
  background: linear-gradient(180deg, var(--store-surface), color-mix(in srgb, var(--store-secondary) 40%, var(--store-surface)));
  box-shadow: var(--store-shadow-hover);
  transform: translateX(-105%);
  transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1);
  z-index: 60;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}}
.nav-drawer.open {{ transform: translateX(0); }}
.nav-drawer h2 {{
  font-family: var(--font-display);
  font-size: 1.15rem;
  margin: 0.5rem 0 1rem;
}}
.nav-drawer .nav-group {{
  margin: 0.85rem 0 0.2rem;
  padding: 0 0.35rem;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--store-muted);
}}
.nav-drawer a {{
  display: block;
  padding: 0.75rem 0.9rem;
  border-radius: 0.75rem;
  color: var(--store-text);
  font-weight: 650;
  transition: background 0.2s ease, transform 0.2s ease;
}}
.nav-drawer a:hover {{
  background: color-mix(in srgb, var(--store-secondary) 70%, transparent);
  text-decoration: none;
  transform: translateX(4px);
}}
.drawer-close {{ align-self: flex-end; }}
.brand-lockup {{
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  text-decoration: none;
  color: var(--store-text);
  max-width: min(14rem, 42vw);
}}
.brand-mark-wrap {{ display: inline-flex; flex-shrink: 0; line-height: 0; }}
.brand-word {{
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.header-auth {{
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  margin-right: 0.35rem;
}}
.header-auth a {{
  font-size: 0.82rem;
  font-weight: 650;
  color: var(--store-text);
  text-decoration: none;
  white-space: nowrap;
}}
.header-auth a:hover {{ color: var(--store-accent); }}
.header-auth .auth-register {{
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  background: var(--store-accent);
  color: #fafaf9 !important;
}}
@media (max-width: 720px) {{
  .header-auth .auth-login-label {{ display: none; }}
}}

/* Hero */
.hero {{
  position: relative;
  padding: 4.5rem 0 3.5rem;
  overflow: hidden;
  background:
    linear-gradient(135deg,
      color-mix(in srgb, var(--store-accent) 22%, var(--store-secondary)) 0%,
      var(--store-secondary) 45%,
      color-mix(in srgb, var(--store-bg) 70%, var(--store-surface)) 100%);
}}
.hero::after {{
  content: "";
  position: absolute;
  width: 28rem;
  height: 28rem;
  right: -6rem;
  top: -4rem;
  border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--store-accent) 35%, transparent), transparent 70%);
  filter: blur(20px);
  pointer-events: none;
}}
.hero-eyebrow {{
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--store-muted);
  margin: 0 0 0.65rem;
}}
.hero h1 {{
  font-family: var(--font-display);
  margin: 0 0 0.85rem;
  font-size: clamp(2rem, 5vw, 3.25rem);
  letter-spacing: -0.03em;
  line-height: 1.15;
  max-width: 16ch;
}}
.hero p {{
  margin: 0 0 1.5rem;
  max-width: 34rem;
  color: var(--store-muted);
  font-size: 1.05rem;
}}
.btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  background: var(--store-accent);
  color: #fff;
  padding: 0.75rem 1.35rem;
  border-radius: 999px;
  font-weight: 600;
  font-size: 0.95rem;
  border: none;
  cursor: pointer;
  box-shadow: 0 8px 24px color-mix(in srgb, var(--store-accent) 35%, transparent);
  transition: transform 0.2s ease, filter 0.2s ease, box-shadow 0.2s ease;
}}
.btn:hover {{
  filter: brightness(1.06);
  text-decoration: none;
  color: #fff;
  transform: translateY(-2px);
  box-shadow: 0 12px 28px color-mix(in srgb, var(--store-accent) 45%, transparent);
}}
.btn-ghost {{
  background: color-mix(in srgb, var(--store-surface) 80%, transparent);
  color: var(--store-text);
  box-shadow: none;
  border: 1px solid color-mix(in srgb, var(--store-secondary) 90%, var(--store-muted));
}}
.btn-ghost:hover {{ color: var(--store-primary); }}
.btn-sm {{ padding: 0.55rem 0.9rem; font-size: 0.82rem; }}
.btn-row {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.85rem; }}

.section {{ padding: 3rem 0; position: relative; z-index: 1; }}
.section-alt {{
  background: color-mix(in srgb, var(--store-secondary) 55%, transparent);
  border-radius: 1.5rem;
  margin: 0 1rem;
  padding: 2.5rem 0;
}}
.section h2, .page-title {{
  font-family: var(--font-display);
  margin: 0 0 1.25rem;
  font-size: clamp(1.45rem, 3vw, 1.85rem);
  letter-spacing: -0.02em;
}}
.page-title {{ margin: 2rem 0 1rem; }}

.cat-strip {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1rem;
}}
.cat-chip {{
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.7rem 1.15rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--store-surface) 88%, #000);
  border: 1px solid color-mix(in srgb, var(--store-accent) 40%, rgba(255,255,255,0.2));
  color: #fafaf9 !important;
  font-weight: 700;
  font-size: 0.95rem;
  letter-spacing: 0.01em;
  box-shadow: 0 10px 28px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.08);
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease, border-color 0.2s ease;
  text-decoration: none !important;
}}
.cat-chip::before {{
  content: "";
  width: 0.45rem; height: 0.45rem; border-radius: 999px;
  background: var(--store-accent);
  box-shadow: 0 0 10px color-mix(in srgb, var(--store-accent) 70%, transparent);
  flex-shrink: 0;
}}
.cat-chip:hover {{
  transform: translateY(-2px);
  background: color-mix(in srgb, var(--store-accent) 26%, var(--store-surface));
  border-color: var(--store-accent);
  box-shadow: 0 14px 32px rgba(0,0,0,0.35);
  text-decoration: none !important;
  color: #fafaf9 !important;
}}
#categories h2, #collections h2 {{
  color: #fafaf9;
  font-family: var(--font-display);
}}
.collections-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}}
.collection-tile {{
  position: relative;
  border-radius: 1.15rem;
  overflow: hidden;
  min-height: 12rem;
  display: flex;
  align-items: flex-end;
  padding: 1.2rem;
  color: #fafaf9 !important;
  text-decoration: none !important;
  background: color-mix(in srgb, var(--store-surface) 85%, #000);
  border: 1px solid color-mix(in srgb, var(--store-accent) 25%, transparent);
}}
.collection-tile img {{
  position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover;
  opacity: 0.55;
}}
.collection-tile::after {{
  content: "";
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.72) 100%);
  z-index: 1;
}}
.collection-tile span {{
  position: relative; z-index: 2;
  font-family: var(--font-display);
  font-size: 1.15rem; font-weight: 700;
  color: #fafaf9 !important;
  text-shadow: 0 2px 16px rgba(0,0,0,0.7);
}}
.collection-tile:hover img {{ opacity: 0.7; transform: scale(1.04); }}
.collection-tile img {{ transition: transform .45s ease, opacity .35s ease; }}

.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1.25rem;
}}
.card {{
  background: color-mix(in srgb, var(--store-surface) 92%, #000) !important;
  border: 1px solid color-mix(in srgb, var(--store-accent) 22%, transparent);
  border-radius: var(--store-radius);
  padding: 0;
  overflow: hidden;
  box-shadow: 0 16px 40px rgba(0,0,0,0.28);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  display: flex;
  flex-direction: column;
  position: relative;
  color: var(--store-text);
}}
.card h3, .card .price, .card strong {{
  color: var(--store-text) !important;
  font-family: var(--font-display);
}}
.card .muted, .card-meta {{
  color: color-mix(in srgb, var(--store-muted) 88%, #fff) !important;
}}
.card:hover {{
  transform: translateY(-6px);
  box-shadow: var(--store-shadow-hover);
}}
.card-media {{
  aspect-ratio: 4 / 3;
  background:
    linear-gradient(145deg,
      color-mix(in srgb, var(--store-accent) 25%, var(--store-secondary)),
      var(--store-secondary) 55%,
      color-mix(in srgb, var(--store-primary) 12%, var(--store-surface)));
  display: block;
  position: relative;
  overflow: hidden;
  min-height: 11rem;
}}
.card-media img,
.card-media.has-product-image img {{
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block !important;
  opacity: 1 !important;
  visibility: visible !important;
  z-index: 2;
}}
.card-media.has-product-image {{
  font-size: 0;
  color: transparent;
  background: #1a1a1a;
}}
.card-body {{
  padding: 1rem 1.05rem 1.15rem;
  color: #fafaf9 !important;
}}
.card-body h3 a {{
  color: #fafaf9 !important;
  text-decoration: none;
  font-family: var(--font-hand, var(--font-display));
}}
.pdp-desc {{
  color: #fafaf9 !important;
  font-size: 1.05rem;
  line-height: 1.7;
  max-width: 42rem;
}}
.review-card {{
  background: #1a1714 !important;
  border-radius: var(--store-radius);
  padding: 1.35rem 1.25rem;
  box-shadow: 0 16px 40px rgba(0,0,0,0.28);
  border: 1px solid color-mix(in srgb, var(--store-accent) 22%, transparent);
  color: #fafaf9 !important;
}}
.review-card .rating {{ margin: 0 0 0.65rem; color: var(--store-accent); }}
.review-card p {{
  margin: 0 0 0.85rem;
  color: #fafaf9 !important;
  font-size: 1.2rem;
  line-height: 1.55;
  font-family: var(--font-hand, var(--font-display));
}}
.review-card cite {{
  font-style: normal;
  font-weight: 600;
  font-size: 0.85rem;
  color: rgba(250,250,249,0.85) !important;
}}
.card {{
  background: #1a1714 !important;
  color: #fafaf9 !important;
}}
.promo-banner {{
  position: relative;
  min-height: 12rem;
  border-radius: 1.25rem;
  overflow: hidden;
  margin: 0 0 0.5rem;
  box-shadow: var(--store-shadow);
}}
.promo-banner img {{
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}}
.promo-banner .promo-inner {{
  position: relative;
  z-index: 1;
  padding: 2.5rem 1.75rem;
  background: linear-gradient(90deg, rgba(8,6,4,0.72) 0%, rgba(8,6,4,0.35) 55%, transparent 100%);
  color: #f8fafc;
  min-height: 12rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.5rem;
}}
.promo-banner h2 {{
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(1.4rem, 3vw, 2rem);
  letter-spacing: -0.02em;
}}
.promo-banner p {{ margin: 0; max-width: 36rem; opacity: 0.92; }}
.hero.has-hero-image {{
  min-height: min(78vh, 820px);
  display: flex;
  align-items: flex-end;
  padding: 0;
  background: #0f172a;
}}
.hero.has-hero-image .hero-photo {{
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
}}
.hero.has-hero-image::before {{
  content: "";
  position: absolute;
  inset: 0;
  z-index: 1;
  background: linear-gradient(105deg, rgba(8,6,4,0.72) 0%, rgba(8,6,4,0.42) 42%, rgba(8,6,4,0.18) 100%);
  pointer-events: none;
}}
.hero.has-hero-image .wrap,
.hero.has-hero-image .hero-offer {{
  position: relative;
  z-index: 2;
  padding: 5rem 1.25rem 3.5rem;
  color: #f8fafc;
}}
.hero.has-hero-image .hero-eyebrow,
.hero.has-hero-image p,
.hero.has-hero-image .hero-why {{
  color: rgba(248, 250, 252, 0.88);
}}
.hero.has-hero-image h1 {{
  color: #fff;
  max-width: 14ch;
}}
.hero.hero-luxury.has-hero-image {{
  min-height: min(92vh, 960px);
}}
.hero.hero-luxury.has-hero-image::before {{
  background: linear-gradient(115deg, rgba(8,6,4,.82) 0%, rgba(8,6,4,.4) 48%, rgba(8,6,4,.15) 100%);
}}
.hero.hero-luxury h1 {{
  font-size: clamp(2.6rem, 6.5vw, 4.2rem);
  letter-spacing: -0.035em;
}}
.hero.hero-luxury .btn {{
  background: linear-gradient(135deg, #c5a572, #a78b5a);
  color: #0c0a09;
  border: 0;
  box-shadow: 0 16px 40px rgba(0,0,0,0.28);
}}
.hero-offer-line {{
  font-size: 1.05rem;
  margin: 0 0 0.5rem;
  max-width: 36rem;
}}
.hero-benefits {{
  list-style: none;
  margin: 0 0 1.35rem;
  padding: 0;
  display: grid;
  gap: 0.35rem;
  max-width: 28rem;
}}
.hero-benefits li {{
  position: relative;
  padding-left: 1.25rem;
  font-size: 0.95rem;
  color: rgba(248, 250, 252, 0.92);
}}
.hero-benefits li::before {{
  content: "✓";
  position: absolute;
  left: 0;
  color: #f0e0c4;
  font-weight: 700;
}}
.hero-cta-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}}
.hero.has-hero-image .btn-ghost.hero-cta-secondary {{
  background: rgba(255,255,255,0.12);
  color: #fff;
  border: 1px solid rgba(255,255,255,0.35);
}}
.trust-bar {{
  background: color-mix(in srgb, var(--store-surface) 92%, #fff);
  border-bottom: 1px solid color-mix(in srgb, var(--store-secondary) 75%, transparent);
}}
.trust-bar-grid {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem 1rem;
  padding: 1rem 1.25rem;
}}
@media (min-width: 900px) {{
  .trust-bar-grid {{ grid-template-columns: repeat(5, minmax(0, 1fr)); }}
}}
.trust-bar-item {{
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}}
.trust-bar-item strong {{
  font-size: 0.82rem;
  letter-spacing: -0.01em;
}}
.trust-bar-item span {{
  font-size: 0.75rem;
  color: var(--store-muted);
  line-height: 1.35;
}}
.badge.hit {{
  background: linear-gradient(135deg, #0f172a, #334155);
  color: #f8fafc;
}}
.card:hover .card-media img {{
  transform: scale(1.04);
}}
.card-media img {{
  transition: transform 0.35s ease;
}}
.pdp-media {{ display: flex; flex-direction: column; gap: 0.75rem; }}
.pdp-thumbs {{
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}}
.pdp-thumb {{
  appearance: none;
  border: 2px solid transparent;
  padding: 0;
  width: 4.25rem;
  height: 4.25rem;
  border-radius: 0.65rem;
  overflow: hidden;
  cursor: pointer;
  background: var(--store-secondary);
}}
.pdp-thumb.is-active {{
  border-color: var(--store-accent);
}}
.pdp-thumb img {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}}
.pdp-gallery {{
  cursor: zoom-in;
  border: none;
  width: 100%;
  padding: 0;
  text-align: left;
}}
.pdp-zoom-hint {{
  position: absolute;
  left: 0.75rem;
  bottom: 0.75rem;
  z-index: 2;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.35rem 0.55rem;
  border-radius: 999px;
  background: rgba(15,23,42,0.65);
  color: #fff;
}}
.pdp-lightbox {{
  position: fixed;
  inset: 0;
  z-index: 80;
  background: rgba(8,6,4,0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}}
.pdp-lightbox[hidden] {{ display: none !important; }}
.pdp-lightbox img {{
  max-width: min(96vw, 960px);
  max-height: 90vh;
  object-fit: contain;
  border-radius: 0.75rem;
}}
.pdp-lightbox-close {{
  position: absolute;
  top: 1rem;
  right: 1rem;
  appearance: none;
  border: none;
  background: rgba(255,255,255,0.15);
  color: #fff;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 999px;
  font-size: 1.4rem;
  cursor: pointer;
}}
.pdp-variants {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin: 1rem 0;
}}
.pdp-variants label {{
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.8rem;
  font-weight: 600;
}}
.pdp-variants select {{
  font: inherit;
  padding: 0.55rem 0.7rem;
  border-radius: 0.65rem;
  border: 1px solid color-mix(in srgb, var(--store-secondary) 90%, var(--store-muted));
  background: var(--store-surface);
}}
.pdp-subhead {{
  font-size: 1.05rem;
  margin: 1.5rem 0 0.5rem;
}}
.pdp-desc {{ margin: 0; color: var(--store-muted); }}
.pdp-cta .btn {{ min-height: 2.75rem; }}
@media (max-width: 719px) {{
  .hero.has-hero-image {{ min-height: auto; }}
  .hero.has-hero-image .wrap,
  .hero.has-hero-image .hero-offer {{ padding-top: 3.5rem; padding-bottom: 2.5rem; }}
  .hero-cta-row .btn {{ flex: 1 1 auto; text-align: center; }}
  .pdp-cta {{
    position: sticky;
    bottom: 4.25rem;
    z-index: 30;
    background: color-mix(in srgb, var(--store-surface) 94%, transparent);
    backdrop-filter: blur(10px);
    padding: 0.65rem 0;
    margin: 0 -0.25rem;
  }}
  .card .btn-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.4rem;
  }}
  .card .btn-sm {{ width: 100%; justify-content: center; }}
}}
.hero.has-hero-image::after {{ display: none; }}
@media (max-width: 720px) {{
  .hero.has-hero-image {{ min-height: auto; }}
}}
.card-body {{ padding: 1.1rem 1.15rem 1.25rem; display: flex; flex-direction: column; flex: 1; }}
.card-body h3 {{
  margin: 0 0 0.35rem;
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}}
.card .price {{
  color: var(--store-accent);
  font-weight: 700;
  font-size: 1.1rem;
  margin: 0.35rem 0 0;
}}
.price-row {{ display: flex; align-items: baseline; gap: 0.5rem; flex-wrap: wrap; }}
.old-price {{
  color: var(--store-muted);
  text-decoration: line-through;
  font-size: 0.9rem;
  font-weight: 500;
}}
.badge {{
  position: absolute;
  top: 0.75rem;
  left: 0.75rem;
  z-index: 2;
  padding: 0.25rem 0.55rem;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  background: var(--store-primary);
  color: #fff;
}}
.badge.sale {{ background: var(--store-accent); }}
.wish-btn {{
  position: absolute;
  top: 0.65rem;
  right: 0.65rem;
  z-index: 2;
  width: 2.1rem;
  height: 2.1rem;
  border-radius: 999px;
  border: none;
  background: color-mix(in srgb, var(--store-surface) 88%, transparent);
  cursor: pointer;
  font-size: 0.95rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transition: transform 0.2s ease;
}}
.wish-btn:hover {{ transform: scale(1.08); }}
.rating {{
  color: #d97706;
  font-size: 0.82rem;
  margin: 0.25rem 0;
}}
.stock {{
  font-size: 0.78rem;
  color: var(--store-muted);
  margin: 0.15rem 0 0.5rem;
}}
.stock.low {{ color: #b45309; font-weight: 600; }}

.trust {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}}
.trust-item {{
  background: var(--store-surface);
  border-radius: var(--store-radius);
  padding: 1.25rem;
  box-shadow: var(--store-shadow);
  border: 1px solid color-mix(in srgb, var(--store-secondary) 70%, transparent);
}}
.trust-item strong {{ display: block; margin-bottom: 0.35rem; }}

.reviews-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.15rem;
}}
/* review-card base moved above with dark readable ink */
.newsletter {{
  background: linear-gradient(120deg, var(--store-primary), color-mix(in srgb, var(--store-accent) 55%, var(--store-primary)));
  color: #fff;
  border-radius: 1.5rem;
  padding: 2.25rem 1.75rem;
  margin: 0 1rem;
}}
.newsletter h2 {{ color: #fff; margin-bottom: 0.5rem; }}
.newsletter p {{ opacity: 0.9; margin: 0 0 1rem; max-width: 32rem; }}
.newsletter-form {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}}
.newsletter-form input {{
  flex: 1;
  min-width: 200px;
  max-width: none;
  border: none;
  border-radius: 999px;
  padding: 0.75rem 1.1rem;
}}
.newsletter .btn {{
  background: color-mix(in srgb, var(--store-accent) 85%, #fff);
  color: #0c0a09;
  box-shadow: none;
}}
.newsletter-form input {{
  background: rgba(8,10,12,0.55) !important;
  color: #fafaf9 !important;
  border: 1px solid rgba(255,255,255,0.18) !important;
}}

.site-footer {{
  margin-top: 2.5rem;
  padding: 2.5rem 0 2rem;
  background: linear-gradient(180deg, transparent, color-mix(in srgb, var(--store-primary) 92%, #000));
  color: color-mix(in srgb, #fff 88%, transparent);
  position: relative;
  z-index: 1;
}}
.site-footer a {{ color: color-mix(in srgb, #fff 90%, var(--store-accent)); }}
.site-footer a:hover {{ color: #fff; }}
.footer-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1.5rem;
  padding-bottom: 1.5rem;
}}
.footer-grid h3 {{
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin: 0 0 0.75rem;
  opacity: 0.75;
  font-weight: 600;
}}
.footer-grid ul {{ list-style: none; margin: 0; padding: 0; }}
.footer-grid li {{ margin: 0.4rem 0; }}
.footer-note {{
  border-top: 1px solid rgba(255,255,255,0.15);
  padding-top: 1rem;
  font-size: 0.85rem;
  opacity: 0.8;
}}

.muted {{ color: var(--store-muted); }}
form label {{ display: block; margin: 0.75rem 0 0.25rem; font-size: 0.9rem; }}
form input, form textarea {{
  width: 100%;
  max-width: 420px;
  padding: 0.6rem 0.75rem;
  border: 1px solid color-mix(in srgb, var(--store-secondary) 90%, var(--store-muted));
  border-radius: 0.65rem;
  background: var(--store-surface);
  font: inherit;
}}

/* PDP */
.pdp {{
  display: grid;
  gap: 2rem;
  grid-template-columns: 1fr;
  padding: 2rem 0 3rem;
}}
@media (min-width: 860px) {{
  .pdp {{ grid-template-columns: 1.05fr 1fr; align-items: start; }}
}}
.pdp-gallery {{
  aspect-ratio: 1;
  border-radius: 1.25rem;
  background:
    linear-gradient(145deg,
      color-mix(in srgb, var(--store-accent) 30%, var(--store-secondary)),
      var(--store-surface));
  box-shadow: var(--store-shadow);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-size: 4rem;
  color: color-mix(in srgb, var(--store-primary) 35%, transparent);
  overflow: hidden;
  position: relative;
}}
.pdp-gallery img {{
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}}
.pdp-gallery.has-product-image {{
  font-size: 0;
  color: transparent;
}}
.specs {{
  margin: 1.25rem 0;
  padding: 0;
  list-style: none;
}}
.specs li {{
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.55rem 0;
  border-bottom: 1px solid color-mix(in srgb, var(--store-secondary) 80%, transparent);
  font-size: 0.92rem;
}}

/* Cart */
.cart-layout {{
  display: grid;
  gap: 1.5rem;
  grid-template-columns: 1fr;
  padding-bottom: 3rem;
}}
@media (min-width: 860px) {{
  .cart-layout {{ grid-template-columns: 1.4fr 0.8fr; align-items: start; }}
}}
.cart-line {{
  display: grid;
  grid-template-columns: 4.5rem 1fr auto;
  gap: 1rem;
  align-items: center;
  background: var(--store-surface);
  border-radius: var(--store-radius);
  padding: 1rem;
  box-shadow: var(--store-shadow);
  margin-bottom: 0.75rem;
}}
.cart-thumb {{
  width: 4.5rem;
  height: 4.5rem;
  border-radius: 0.75rem;
  background: linear-gradient(135deg, var(--store-secondary), color-mix(in srgb, var(--store-accent) 25%, var(--store-surface)));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: var(--store-muted);
}}
.qty-ctrl {{
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.35rem;
}}
.qty-ctrl button {{
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 0.45rem;
  border: 1px solid var(--store-secondary);
  background: var(--store-bg);
  cursor: pointer;
}}
.cart-summary {{
  background: var(--store-surface);
  border-radius: 1.25rem;
  padding: 1.5rem;
  box-shadow: var(--store-shadow);
  position: sticky;
  top: 5rem;
}}
.cart-summary .total {{
  font-size: 1.35rem;
  font-weight: 700;
  margin: 1rem 0;
}}
.toast {{
  position: fixed;
  bottom: 1.25rem;
  right: 1.25rem;
  background: var(--store-primary);
  color: #fff;
  padding: 0.75rem 1.1rem;
  border-radius: 0.75rem;
  box-shadow: var(--store-shadow-hover);
  z-index: 80;
  opacity: 0;
  transform: translateY(12px);
  transition: opacity 0.25s ease, transform 0.25s ease;
  pointer-events: none;
}}
.toast.show {{ opacity: 1; transform: translateY(0); }}
.checkout-note {{
  display: none;
  margin-top: 0.85rem;
  padding: 0.85rem;
  border-radius: 0.75rem;
  background: color-mix(in srgb, var(--store-secondary) 70%, transparent);
  font-size: 0.9rem;
  color: var(--store-muted);
}}
.checkout-note.show {{ display: block; }}

/* Wishlist panel on cart page */
.wish-panel {{
  margin-top: 2.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid color-mix(in srgb, var(--store-secondary) 80%, transparent);
}}
.wish-panel h2 {{
  font-family: var(--font-display);
  font-size: 1.25rem;
  margin: 0 0 1rem;
}}
.wish-line {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem 1rem;
  margin-bottom: 0.65rem;
  background: var(--store-surface);
  border-radius: 0.85rem;
  box-shadow: 0 4px 16px rgba(28,25,23,0.04);
}}
.wish-line:target, #wishlist:target ~ .wish-panel,
.wish-panel:target {{
  outline: 2px solid color-mix(in srgb, var(--store-accent) 40%, transparent);
  outline-offset: 4px;
  border-radius: 1rem;
}}

/* Mobile bottom bar — cart always reachable */
.mobile-bar {{
  display: none;
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 45;
  background: color-mix(in srgb, var(--store-surface) 92%, transparent);
  backdrop-filter: blur(12px);
  border-top: 1px solid color-mix(in srgb, var(--store-secondary) 75%, transparent);
  padding: 0.45rem 0.75rem calc(0.45rem + env(safe-area-inset-bottom));
  justify-content: space-around;
  gap: 0.35rem;
}}
.mobile-bar a {{
  flex: 1;
  text-align: center;
  color: var(--store-text);
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.35rem 0.25rem;
  border-radius: 0.65rem;
  text-decoration: none;
  position: relative;
}}
.mobile-bar a:hover {{ background: var(--store-secondary); text-decoration: none; }}
.mobile-bar .mb-ico {{ display: block; font-size: 1.15rem; line-height: 1.2; }}
@media (max-width: 719px) {{
  .mobile-bar {{ display: flex; }}
  body {{ padding-bottom: 4.5rem; }}
  .toast {{ bottom: 5rem; }}
  .site-header-inner {{ flex-wrap: wrap; }}
  .header-search {{
    display: block;
    order: 5;
    flex: 1 1 100%;
  }}
}}
{niche_css}
"""


def compose_store_js(ui: dict[str, str] | None = None) -> str:
    u = ui or ui_copy({})
    # Escape for embedding inside a JS string literal
    def j(key: str) -> str:
        return json.dumps(u.get(key, ""), ensure_ascii=False)

    return f"""/* AI Store R2.1 — cart, drawer, wishlist (localStorage) */
(function () {{
  var CART_KEY = "store_cart_v1";
  var WISH_KEY = "store_wish_v1";
  var RECENT_KEY = "store_recent_v1";
  var UI = {{
    toastAdded: {j("toast_added")},
    toastWishAdd: {j("toast_wish_add")},
    toastWishRm: {j("toast_wish_rm")},
    toastCheckout: {j("toast_checkout")},
    toastPromo: {j("toast_promo")},
    remove: {j("remove")},
    wishEmpty: {j("wish_empty")},
    browse: {j("browse")}
  }};

  function read(key) {{
    try {{
      var raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : [];
    }} catch (e) {{
      return [];
    }}
  }}
  function write(key, val) {{
    localStorage.setItem(key, JSON.stringify(val));
  }}

  function cart() {{ return read(CART_KEY); }}
  function setCart(items) {{
    write(CART_KEY, items);
    updateBadge();
    renderCartPage();
  }}

  function updateBadge() {{
    var items = cart();
    var n = items.reduce(function (s, it) {{ return s + (it.qty || 1); }}, 0);
    document.querySelectorAll("[data-cart-badge]").forEach(function (el) {{
      el.textContent = String(n);
      el.setAttribute("data-count", String(n));
      el.classList.toggle("has-items", n > 0);
    }});
  }}

  function toast(msg) {{
    var el = document.getElementById("store-toast");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(el._t);
    el._t = setTimeout(function () {{ el.classList.remove("show"); }}, 1800);
  }}

  function addItem(payload, buyNow) {{
    var items = cart();
    var found = items.find(function (x) {{ return x.id === payload.id; }});
    if (found) found.qty = (found.qty || 1) + 1;
    else items.push({{ id: payload.id, name: payload.name, price: payload.price, priceLabel: payload.priceLabel, qty: 1 }});
    setCart(items);
    toast(UI.toastAdded);
    if (buyNow) window.location.href = "cart.html";
  }}

  function toggleWish(id, name) {{
    if (!id || id === "header") return;
    var list = read(WISH_KEY);
    var i = list.findIndex(function (x) {{ return x.id === id; }});
    if (i >= 0) list.splice(i, 1);
    else list.push({{ id: id, name: name }});
    write(WISH_KEY, list);
    toast(i >= 0 ? UI.toastWishRm : UI.toastWishAdd);
    renderWishPage();
  }}

  function renderWishPage() {{
    var root = document.getElementById("wish-lines");
    if (!root) return;
    var list = read(WISH_KEY).filter(function (x) {{ return x && x.id && x.id !== "header"; }});
    var empty = document.getElementById("wish-empty");
    if (!list.length) {{
      root.innerHTML = "";
      if (empty) empty.style.display = "block";
      return;
    }}
    if (empty) empty.style.display = "none";
    root.innerHTML = list.map(function (it) {{
      return (
        '<div class="wish-line" data-wish-id="' + escapeHtml(it.id) + '">' +
          "<strong>" + escapeHtml(it.name || it.id) + "</strong>" +
          '<button type="button" class="btn btn-ghost btn-sm" data-action="wish" data-id="' +
          escapeHtml(it.id) + '" data-name="' + escapeHtml(it.name || "") + '">' +
          escapeHtml(UI.remove) + "</button>" +
        "</div>"
      );
    }}).join("");
  }}

  function openDrawer(open) {{
    var d = document.getElementById("nav-drawer");
    var o = document.getElementById("drawer-overlay");
    if (!d || !o) return;
    d.classList.toggle("open", open);
    o.classList.toggle("open", open);
    document.body.style.overflow = open ? "hidden" : "";
  }}

  function renderCartPage() {{
    var root = document.getElementById("cart-lines");
    if (!root) return;
    var items = cart();
    var empty = document.getElementById("cart-empty");
    var summary = document.getElementById("cart-summary");
    if (!items.length) {{
      root.innerHTML = "";
      if (empty) empty.style.display = "block";
      if (summary) summary.style.display = "none";
      return;
    }}
    if (empty) empty.style.display = "none";
    if (summary) summary.style.display = "block";
    var total = 0;
    root.innerHTML = items.map(function (it) {{
      var line = (it.price || 0) * (it.qty || 1);
      total += line;
      var letter = (it.name || "?").charAt(0).toUpperCase();
      return (
        '<article class="cart-line" data-id="' + it.id + '">' +
          '<div class="cart-thumb">' + letter + "</div>" +
          '<div><strong>' + escapeHtml(it.name) + "</strong>" +
          '<div class="muted">' + escapeHtml(it.priceLabel || "") + "</div>" +
          '<div class="qty-ctrl">' +
            '<button type="button" data-qty="-1" aria-label="−">−</button>' +
            "<span>" + (it.qty || 1) + "</span>" +
            '<button type="button" data-qty="1" aria-label="+">+</button>' +
          "</div></div>" +
          '<div><strong>€' + line.toFixed(2) + "</strong><br>" +
          '<button type="button" class="btn btn-ghost btn-sm" data-remove style="margin-top:0.5rem">' +
          escapeHtml(UI.remove) + "</button></div>" +
        "</article>"
      );
    }}).join("");
    var totalEl = document.getElementById("cart-total");
    if (totalEl) totalEl.textContent = "€" + total.toFixed(2);
  }}

  function escapeHtml(s) {{
    return String(s || "").replace(/[&<>"']/g, function (c) {{
      return ({{ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }})[c];
    }});
  }}

  function filterCatalog(q) {{
    q = (q || "").trim().toLowerCase();
    var cards = document.querySelectorAll("[data-product-card]");
    if (!cards.length && q) {{
      window.location.href = "catalog.html?q=" + encodeURIComponent(q);
      return;
    }}
    cards.forEach(function (card) {{
      var name = (card.getAttribute("data-name") || "").toLowerCase();
      card.style.display = !q || name.indexOf(q) >= 0 ? "" : "none";
    }});
  }}

  document.addEventListener("click", function (e) {{
    var navLink = e.target.closest(".nav-drawer a");
    if (navLink) openDrawer(false);

    var t = e.target.closest("[data-action]");
    if (t) {{
      var action = t.getAttribute("data-action");
      if (action === "drawer-open") openDrawer(true);
      if (action === "drawer-close") openDrawer(false);
      if (action === "add-cart" || action === "buy-now") {{
        addItem({{
          id: t.getAttribute("data-id"),
          name: t.getAttribute("data-name"),
          price: parseFloat(t.getAttribute("data-price") || "0"),
          priceLabel: t.getAttribute("data-price-label") || ""
        }}, action === "buy-now");
      }}
      if (action === "wish") {{
        toggleWish(t.getAttribute("data-id"), t.getAttribute("data-name"));
      }}
      if (action === "checkout") {{
        window.location.href = "checkout.html";
      }}
    }}
    var line = e.target.closest(".cart-line");
    if (line) {{
      var id = line.getAttribute("data-id");
      var items = cart();
      if (e.target.closest("[data-remove]")) {{
        setCart(items.filter(function (x) {{ return x.id !== id; }}));
        return;
      }}
      var qtyBtn = e.target.closest("[data-qty]");
      if (qtyBtn) {{
        var delta = parseInt(qtyBtn.getAttribute("data-qty"), 10);
        items = items.map(function (x) {{
          if (x.id !== id) return x;
          return Object.assign({{}}, x, {{ qty: Math.max(1, (x.qty || 1) + delta) }});
        }});
        setCart(items);
      }}
    }}
  }});

  var overlay = document.getElementById("drawer-overlay");
  if (overlay) overlay.addEventListener("click", function () {{ openDrawer(false); }});

  var search = document.getElementById("header-search");
  if (search) {{
    var params = new URLSearchParams(window.location.search);
    var q0 = params.get("q");
    if (q0) {{
      search.value = q0;
      filterCatalog(q0);
    }}
    search.addEventListener("input", function () {{ filterCatalog(search.value); }});
    search.addEventListener("keydown", function (ev) {{
      if (ev.key === "Enter") {{
        ev.preventDefault();
        filterCatalog(search.value);
      }}
    }});
  }}

  var promo = document.getElementById("promo-apply");
  if (promo) {{
    promo.addEventListener("click", function () {{
      toast(UI.toastPromo);
    }});
  }}

  updateBadge();
  renderCartPage();
  renderWishPage();

  /* PDP gallery + zoom */
  document.addEventListener("click", function (e) {{
    var thumb = e.target.closest(".pdp-thumb");
    if (thumb) {{
      var src = thumb.getAttribute("data-pdp-src");
      var main = document.getElementById("pdp-main-img");
      var light = document.getElementById("pdp-lightbox-img");
      if (src && main) main.src = src;
      if (src && light) light.src = src;
      document.querySelectorAll(".pdp-thumb").forEach(function (t) {{
        t.classList.toggle("is-active", t === thumb);
      }});
    }}
    if (e.target.closest("[data-action='pdp-zoom']")) {{
      var box = document.getElementById("pdp-lightbox");
      if (box) box.hidden = false;
    }}
    if (e.target.closest("[data-action='pdp-zoom-close']") || e.target.id === "pdp-lightbox") {{
      var box2 = document.getElementById("pdp-lightbox");
      if (box2 && (e.target.id === "pdp-lightbox" || e.target.closest("[data-action='pdp-zoom-close']"))) {{
        box2.hidden = true;
      }}
    }}
  }});

  /* Recently viewed */
  (function trackRecent() {{
    var root = document.querySelector(".pdp[data-product-id]");
    if (root) {{
      var entry = {{
        id: root.getAttribute("data-product-id"),
        name: root.getAttribute("data-product-name"),
        image: root.getAttribute("data-product-image"),
        priceLabel: root.getAttribute("data-product-price")
      }};
      var list = read(RECENT_KEY).filter(function (x) {{ return x && x.id && x.id !== entry.id; }});
      list.unshift(entry);
      write(RECENT_KEY, list.slice(0, 8));
    }}
    var grid = document.querySelector("[data-recent-grid]");
    if (!grid) return;
    var items = read(RECENT_KEY).filter(function (x) {{
      return x && x.id && (!root || x.id !== root.getAttribute("data-product-id"));
    }}).slice(0, 4);
    if (!items.length) {{
      grid.closest("section").style.display = "none";
      return;
    }}
    grid.innerHTML = items.map(function (it) {{
      var img = it.image
        ? '<a href="product.html?id=' + escapeHtml(it.id) + '" class="card-media has-product-image"><img src="' +
          escapeHtml(it.image) + '" alt="' + escapeHtml(it.name || "") + '" loading="lazy" /></a>'
        : '<a href="product.html?id=' + escapeHtml(it.id) + '" class="card-media"></a>';
      return (
        '<article class="card" data-product-card data-name="' + escapeHtml(it.name || "") + '">' +
        img +
        '<div class="card-body"><h3><a href="product.html?id=' + escapeHtml(it.id) + '">' +
        escapeHtml(it.name || it.id) + "</a></h3>" +
        '<p class="price">' + escapeHtml(it.priceLabel || "") + "</p></div></article>"
      );
    }}).join("");
  }})();
}})();
"""


def _drawer_links(files: list[str], ui: dict[str, str]) -> str:
    """Left drawer — shop → account → info → legal (Owner: correct section order)."""
    labels = {
        "index.html": ui["home"],
        "catalog.html": ui["catalog"],
        "cart.html": ui["cart"],
        "about.html": ui["about"],
        "contact.html": ui["contact"],
        "faq.html": ui["faq"],
        "impressum.html": "Impressum",
        "datenschutz.html": ui["privacy"],
        "returns.html": ui["returns"],
        "news.html": ui["news"],
        "blog.html": ui["blog"],
    }
    file_set = set(files)

    def link(href: str, label: str) -> str:
        return f'<a href="{_esc(href)}">{_esc(label)}</a>'

    def group(title: str, items: list[str]) -> str:
        if not items:
            return ""
        return (
            f'<p class="nav-group">{_esc(title)}</p>\n      '
            + "\n      ".join(items)
        )

    shop: list[str] = []
    if "index.html" in file_set or True:
        shop.append(link("index.html", labels["index.html"]))
    if "catalog.html" in file_set:
        shop.append(link("catalog.html", labels["catalog.html"]))
        shop.append(link("catalog.html#deals", ui["deals"]))
        shop.append(link("index.html#featured", ui.get("featured") or "Featured"))
    if "cart.html" in file_set:
        shop.append(link("cart.html", labels["cart.html"]))

    account = [
        link("account.html#login", ui.get("login") or "Sign in"),
        link("account.html#register", ui.get("register") or "Register"),
        link("account.html", ui.get("account") or "Account"),
        link("cart.html#wishlist", ui["wishlist"]),
    ]

    info: list[str] = []
    for f in ("about.html", "contact.html", "faq.html", "news.html", "blog.html"):
        if f in file_set:
            info.append(link(f, labels[f]))

    legal: list[str] = []
    for f in ("returns.html", "impressum.html", "datenschutz.html"):
        if f in file_set:
            legal.append(link(f, labels[f]))

    parts = [
        group(ui.get("nav_shop") or "Shop", shop),
        group(ui.get("nav_account") or "Account", account),
        group(ui.get("nav_info") or "Info", info),
        group(ui.get("nav_legal") or "Legal", legal),
    ]
    return "\n      ".join(p for p in parts if p)


def _footer_links(
    files: list[str],
    store_name: str,
    payments: str,
    shipping: str,
    ui: dict[str, str],
) -> str:
    legal = []
    for f, label in (
        ("impressum.html", "Impressum"),
        ("datenschutz.html", ui["privacy"]),
        ("returns.html", ui["returns"]),
        ("faq.html", ui["faq"]),
        ("contact.html", ui["contact"]),
    ):
        if f in files:
            legal.append(f'<li><a href="{_esc(f)}">{_esc(label)}</a></li>')
    legal_html = "\n            ".join(legal) or "<li>—</li>"
    return f"""    <div class="wrap footer-grid">
      <div>
        <h3>{_esc(ui["shop"])}</h3>
        <ul>
          <li><a href="index.html">{_esc(ui["home"])}</a></li>
          <li><a href="catalog.html">{_esc(ui["catalog"])}</a></li>
          <li><a href="cart.html">{_esc(ui["cart"])}</a></li>
          <li><a href="account.html#login">{_esc(ui.get("login") or "Sign in")}</a></li>
          <li><a href="account.html#register">{_esc(ui.get("register") or "Register")}</a></li>
          <li><a href="account.html">{_esc(ui.get("account") or "Account")}</a></li>
        </ul>
      </div>
      <div>
        <h3>{_esc(ui["service"])}</h3>
        <ul>
          {legal_html}
        </ul>
      </div>
      <div>
        <h3>{_esc(ui["pay_ship"])}</h3>
        <ul>
          <li>{_esc(payments)}</li>
          <li>{_esc(shipping)}</li>
        </ul>
      </div>
      <div>
        <h3>{_esc(store_name)}</h3>
        <ul>
          <li>{_esc(ui["powered"])}</li>
        </ul>
      </div>
    </div>
    <div class="wrap footer-note">
      <p>{_esc(store_name)} — Virtus Core AI Store</p>
    </div>"""


def _shell(
    *,
    title: str,
    description: str,
    store_name: str,
    drawer: str,
    body: str,
    ui: dict[str, str],
    footer_extra: str = "",
    niche_id: str = "generic",
    hero_layout: str = "editorial",
    catalog_layout: str = "dense",
    card_preset: str = "general",
    show_certs: bool = False,
    font_head: str = "",
    package_id: str = "business",
    dna_attrs: str = "",
    dna_atm: str = "",
    canvas: str = "light",
    brand_html: str = "",
) -> str:
    lang = ui.get("lang") or "en"
    certs_attr = "1" if show_certs else "0"
    pid = (package_id or "business").strip().lower() or "business"
    motion = (
        "premium" if pid == "premium" else "business" if pid == "business" else "basic"
    )
    canvas_mode = "dark" if (canvas or "").strip().lower() == "dark" else "light"
    extra_dna = f" {dna_attrs.strip()}" if (dna_attrs or "").strip() else ""
    brand = brand_html or f'<a class="brand" href="index.html">{_esc(store_name)}</a>'
    login_lbl = ui.get("login") or "Sign in"
    register_lbl = ui.get("register") or "Register"
    return f"""<!DOCTYPE html>
<html lang="{_esc(lang)}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_esc(title)}</title>
  <meta name="description" content="{_esc(description)}" />
{font_head}  <link rel="stylesheet" href="assets/store.css" />
</head>
<body data-tier="{_esc(pid)}" data-niche="{_esc(niche_id)}" data-canvas="{canvas_mode}" data-hero-layout="{_esc(hero_layout)}" data-catalog="{_esc(catalog_layout)}" data-card="{_esc(card_preset)}" data-certs="{certs_attr}" data-vie-engine="visual_intelligence_v1" data-vie-surface="store" data-vie-niche="{_esc(niche_id)}" data-vie-motion="{_esc(motion)}" class="vie-motion-{_esc(motion)}"{extra_dna}>
{dna_atm}
  <div class="drawer-overlay" id="drawer-overlay" data-action="drawer-close"></div>
  <aside class="nav-drawer" id="nav-drawer" aria-label="Main">
    <button type="button" class="icon-btn drawer-close" data-action="drawer-close" aria-label="{_esc(ui["menu_close"])}">✕</button>
    <h2>{_esc(store_name)}</h2>
    <nav class="nav">
      {drawer}
    </nav>
  </aside>

  <header class="site-header">
    <div class="wrap site-header-inner">
      <button type="button" class="icon-btn" data-action="drawer-open" aria-label="{_esc(ui["menu_open"])}">☰</button>
      {brand}
      <div class="header-search">
        <input id="header-search" type="search" placeholder="{_esc(ui["search_ph"])}" aria-label="{_esc(ui["search_ph"])}" />
      </div>
      <div class="header-actions">
        <div class="header-auth">
          <a class="auth-login" href="account.html#login"><span class="auth-login-label">{_esc(login_lbl)}</span></a>
          <a class="auth-register" href="account.html#register">{_esc(register_lbl)}</a>
        </div>
        <a class="icon-btn" href="account.html" aria-label="{_esc(ui.get("account") or "Account")}" title="{_esc(ui.get("account") or "Account")}">👤</a>
        <a class="icon-btn" href="cart.html#wishlist" aria-label="{_esc(ui["wishlist"])}" title="{_esc(ui["wishlist"])}">♡</a>
        <a class="icon-btn" href="cart.html" aria-label="{_esc(ui["cart"])}" title="{_esc(ui["cart"])}">
          🛒
          <span class="cart-badge" data-cart-badge data-count="0">0</span>
        </a>
      </div>
    </div>
  </header>

  <main>
{body}
  </main>

  <footer class="site-footer">
{footer_extra}
  </footer>
  <nav class="mobile-bar" aria-label="Mobile">
    <a href="index.html"><span class="mb-ico">⌂</span>{_esc(ui["home"])}</a>
    <a href="catalog.html"><span class="mb-ico">▦</span>{_esc(ui["catalog"])}</a>
    <a href="cart.html#wishlist"><span class="mb-ico">♡</span>{_esc(ui["wishlist"])}</a>
    <a href="account.html"><span class="mb-ico">👤</span>{_esc(ui.get("account") or "Account")}</a>
    <a href="cart.html"><span class="mb-ico">🛒</span>{_esc(ui["cart"])}<span class="cart-badge" data-cart-badge data-count="0">0</span></a>
  </nav>
  <div class="toast" id="store-toast" role="status"></div>
  <script src="assets/store.js"></script>
</body>
</html>
"""


def _stars(rating: float) -> str:
    full = int(round(float(rating)))
    full = max(0, min(5, full))
    return "★" * full + "☆" * (5 - full)


def _localize_stock(stock: str, ui: dict[str, str]) -> str:
    s = (stock or "").strip().lower()
    if "few" in s or "wenig" in s:
        return ui["few_left"]
    if "stock" in s or "lager" in s or not s:
        return ui["in_stock"]
    return stock


def _localize_badge(badge: str, ui: dict[str, str]) -> str:
    b = (badge or "").strip().upper()
    if b == "NEW":
        return ui["badge_new"]
    if b == "SALE":
        return ui["badge_sale"]
    if b in ("HIT", "BESTSELLER", "HOT"):
        return ui.get("badge_hit") or "HIT"
    return badge


def _product_cards(products: list[dict[str, Any]], ui: dict[str, str]) -> str:
    bits = []
    for p in products:
        pid = _esc(p.get("id"))
        name = _esc(p.get("name"))
        price = p.get("price") or 0
        price_label = _esc(p.get("price_label"))
        old = _esc(p.get("old_price_label") or "")
        badge = _localize_badge(str(p.get("badge") or ""), ui)
        badge_html = ""
        if badge:
            raw = str(p.get("badge") or "").upper()
            cls = "badge"
            if raw == "SALE":
                cls = "badge sale"
            elif raw in ("HIT", "BESTSELLER", "HOT"):
                cls = "badge hit"
            badge_html = f'<span class="{cls}">{_esc(badge)}</span>'
        rating = float(p.get("rating") or 4.5)
        reviews = int(p.get("reviews") or 0)
        stock = _localize_stock(str(p.get("stock") or "In stock"), ui)
        stock_cls = "stock low" if "few" in stock.lower() or "wenig" in stock.lower() else "stock"
        letter = _esc((str(p.get("name") or "?")[:1]).upper())
        old_html = f'<span class="old-price">{old}</span>' if old else ""
        meta = _esc(str(p.get("card_meta") or ""))
        meta_html = f'<p class="card-meta">{meta}</p>' if meta else ""
        img = str(p.get("image") or p.get("image_slot") or "").strip()
        if img and not img.startswith(("http://", "https://", "assets/", "/", "data:")):
            img = f"assets/images/{img.lstrip('/')}"
        if img:
            media = (
                f'<a href="product.html?id={pid}" class="card-media product-media-slot has-product-image">'
                f'<img src="{_esc(img)}" alt="{name}" width="800" height="1000" '
                f'loading="eager" decoding="async" '
                f'onerror="this.onerror=null;this.src=\'assets/images/missing.jpg\';'
                f'this.alt=\'Bild fehlt — Image missing\'" /></a>'
            )
        else:
            media = (
                f'<a href="product.html?id={pid}" class="card-media product-media-slot" '
                f'aria-hidden="true">{letter}</a>'
            )
        bits.append(
            f"""    <article class="card" data-product-card data-name="{name}" data-id="{pid}">
      {badge_html}
      <button type="button" class="wish-btn" data-action="wish" data-id="{pid}" data-name="{name}" aria-label="{_esc(ui["wishlist"])}">♡</button>
      {media}
      <div class="card-body">
        <h3><a href="product.html?id={pid}">{name}</a></h3>
        {meta_html}
        <p class="rating">{_stars(rating)} <span class="muted">({reviews})</span></p>
        <p class="{stock_cls}">{_esc(stock)}</p>
        <div class="price-row">
          <p class="price">{price_label}</p>
          {old_html}
        </div>
        <div class="btn-row">
          <button type="button" class="btn btn-sm" data-action="add-cart" data-id="{pid}" data-name="{name}" data-price="{price}" data-price-label="{price_label}">{_esc(ui["add_cart"])}</button>
          <button type="button" class="btn btn-ghost btn-sm" data-action="buy-now" data-id="{pid}" data-name="{name}" data-price="{price}" data-price-label="{price_label}">{_esc(ui["buy_now"])}</button>
        </div>
      </div>
    </article>"""
        )
    return "\n".join(bits)


def _reviews_section(ui: dict[str, str]) -> str:
    cards = []
    for i in (1, 2, 3):
        cards.append(
            f"""      <blockquote class="review-card">
        <p class="rating">★★★★★</p>
        <p>{_esc(ui[f"review_{i}_text"])}</p>
        <cite>{_esc(ui[f"review_{i}_name"])}</cite>
      </blockquote>"""
        )
    return f"""  <section class="section section-alt" id="reviews">
    <div class="wrap">
      <h2>{_esc(ui["reviews"])}</h2>
      <div class="reviews-grid">
{chr(10).join(cards)}
      </div>
    </div>
  </section>"""


def _category_strip(labels: tuple[str, ...] | list[str]) -> str:
    chips = "\n".join(
        f'      <a class="cat-chip" href="catalog.html">{_esc(lab)}</a>' for lab in labels[:6]
    )
    return f'<div class="cat-strip">\n{chips}\n    </div>'


def _trust_bar(
    ui: dict[str, str],
    *,
    payments: str,
    shipping: str,
    email: str = "",
) -> str:
    contact = email or ui.get("trust_contact_detail") or ""
    items = [
        (ui["trust_delivery"], ui["trust_delivery_detail"] or shipping),
        (ui["trust_returns"], ui["trust_returns_detail"]),
        (ui["trust_pay"], ui["trust_pay_detail"] or payments),
        (ui["trust_guarantee"], ui["trust_guarantee_detail"]),
        (ui["trust_contact"], contact),
    ]
    cells = "\n".join(
        f"""      <div class="trust-bar-item">
        <strong>{_esc(title)}</strong>
        <span>{_esc(detail)}</span>
      </div>"""
        for title, detail in items
    )
    return f"""  <section class="trust-bar" id="trust" aria-label="{_esc(ui["why_us"])}">
    <div class="wrap trust-bar-grid">
{cells}
    </div>
  </section>"""


def _hero_offer_block(
    *,
    ui: dict[str, str],
    store_name: str,
    what: str,
    hero_line: str,
    eyebrow: str,
    cta_label: str,
    emotional: bool = False,
) -> str:
    if emotional:
        # Brand-first: no benefit bullet list on Premium first fold
        return f"""    <div class="wrap hero-offer">
      <p class="hero-eyebrow">{_esc(eyebrow or ui.get("collections_title") or "")}</p>
      <h1>{_esc(store_name)}</h1>
      <p class="hero-offer-line"><strong>{_esc(what)}</strong></p>
      <p class="hero-why">{_esc(hero_line)}</p>
      <div class="hero-cta-row">
        <a class="btn" href="catalog.html">{_esc(ui.get("cta_catalog") or cta_label)}</a>
        <a class="btn btn-ghost hero-cta-secondary" href="#brand-story">{_esc(ui.get("brand_story_title") or "Story")}</a>
      </div>
    </div>"""
    benefits = "\n".join(
        f"        <li>{_esc(ui[k])}</li>"
        for k in ("hero_benefit_1", "hero_benefit_2", "hero_benefit_3", "hero_benefit_4")
    )
    return f"""    <div class="wrap hero-offer">
      <p class="hero-eyebrow">{_esc(eyebrow)}</p>
      <h1>{_esc(store_name)}</h1>
      <p class="hero-offer-line"><strong>{_esc(what)}</strong></p>
      <p class="hero-why">{_esc(ui["hero_why"])}: {_esc(hero_line)}</p>
      <ul class="hero-benefits">
{benefits}
      </ul>
      <div class="hero-cta-row">
        <a class="btn" href="catalog.html">{_esc(ui.get("cta_catalog") or cta_label)}</a>
        <a class="btn btn-ghost hero-cta-secondary" href="catalog.html">{_esc(ui.get("cta_buy") or ui["buy_now"])}</a>
      </div>
    </div>"""


def _pdp_gallery_html(
    *,
    name: str,
    letter: str,
    images: list[str],
    zoom_hint: str,
) -> str:
    imgs = [i for i in images if i]
    if not imgs:
        return f'<div class="pdp-gallery" aria-label="Product gallery">{letter}</div>'
    main = imgs[0]
    thumbs = "\n".join(
        f'        <button type="button" class="pdp-thumb{" is-active" if i == 0 else ""}" '
        f'data-pdp-src="{_esc(src)}" aria-label="Photo {i + 1}">'
        f'<img src="{_esc(src)}" alt="" width="120" height="120" loading="lazy" /></button>'
        for i, src in enumerate(imgs[:5])
    )
    return f"""    <div class="pdp-media">
      <button type="button" class="pdp-gallery has-product-image" id="pdp-zoom-trigger" data-action="pdp-zoom" aria-label="{_esc(zoom_hint)}">
        <img id="pdp-main-img" src="{_esc(main)}" alt="{name}" width="1000" height="1000" decoding="async" />
        <span class="pdp-zoom-hint">{_esc(zoom_hint)}</span>
      </button>
      <div class="pdp-thumbs" role="list">
{thumbs}
      </div>
    </div>
    <div class="pdp-lightbox" id="pdp-lightbox" hidden>
      <button type="button" class="pdp-lightbox-close" data-action="pdp-zoom-close" aria-label="Close">×</button>
      <img id="pdp-lightbox-img" src="{_esc(main)}" alt="{name}" />
    </div>"""


def write_storefront(
    product_dir: Path,
    *,
    brief: dict[str, Any],
    resolved: ResolvedTemplate,
) -> list[str]:
    """Write HTML + CSS + JS into product_dir. Returns list of written filenames."""
    store_name = str(brief.get("store_name") or "Store")
    company = str(brief.get("company_name") or store_name)
    what = str(brief.get("what_is_sold") or "Quality products")
    category = str(brief.get("category") or "other")
    description = f"{store_name} — {what}"[:160]
    ui = ui_copy(brief)
    files = pages_for_brief(brief)
    drawer = _drawer_links(files, ui)
    theme = resolved.theme
    payments = ", ".join(str(x) for x in (brief.get("payments") or [])) or "Stripe"
    shipping = ", ".join(str(x) for x in (brief.get("shipping") or [])) or "Standard"
    footer = _footer_links(files, store_name, payments, shipping, ui)

    assets = product_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    package_id = str(brief.get("package_id") or "business").strip().lower() or "business"

    # Business Generation — invent a living store brand for demos
    fabricated = brief.get("fabricated_company") if isinstance(brief.get("fabricated_company"), dict) else None
    if brief.get("demo_gallery") or brief.get("fabricate_company"):
        if not fabricated:
            from app.factory.company_fabrication import fabricate_company

            company_obj = fabricate_company(
                niche_id=str(brief.get("category") or resolved.niche_id or "fashion"),
                city=str(brief.get("city") or "Berlin"),
                package_id=package_id,
                diversity_salt=str(brief.get("diversity_salt") or ""),
                prefer_name=str(brief.get("store_name") or ""),
            )
            fabricated = company_obj.as_dict()
            brief["fabricated_company"] = fabricated
            brief["store_name"] = company_obj.brand_name
            brief["company_name"] = company_obj.legal_name
            store_name = company_obj.brand_name
            company = company_obj.legal_name
            try:
                (product_dir / "fabricated_company.json").write_text(
                    __import__("json").dumps(fabricated, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            except OSError:
                pass
        else:
            store_name = str(fabricated.get("brand_name") or store_name)
            company = str(fabricated.get("legal_name") or company)

    if isinstance(fabricated, dict) and fabricated.get("reviews"):
        for i, pair in enumerate(fabricated.get("reviews") or [], start=1):
            if i > 3:
                break
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                ui[f"review_{i}_text"] = str(pair[0])
                ui[f"review_{i}_name"] = str(pair[1])

    from app.factory.design_dna.art_director import run_digital_creative_studio
    from app.factory.design_dna.concept_gate import (
        REALITY_BENCHMARK_NOTE,
        gate_report,
        should_export_marketing_html,
    )
    from app.factory.design_dna.creative_identity import (
        invent_creative_identity,
        write_creative_identity,
        write_identity_preview_as_index,
    )
    from app.factory.design_dna.quality_floor import atmosphere_html, store_quality_floor_css

    studio = run_digital_creative_studio(
        business_name=store_name,
        niche_id=resolved.niche_id or category,
        package_id=package_id,
        diversity_salt=str(brief.get("diversity_salt") or ""),
        product_dir=product_dir,
        surface="store",
    )
    store_dna = studio.dna
    if store_dna is None:
        from app.factory.design_dna import resolve_design_dna
        from app.factory.design_dna.brand_book import (
            apply_brand_book_to_dna,
            resolve_brand_book,
        )

        store_dna = resolve_design_dna(
            business_name=store_name,
            niche_id=resolved.niche_id or category,
            package_id=package_id,
            section_keys=("hero", "catalog", "trust", "reviews", "about", "contact"),
            diversity_salt=str(brief.get("diversity_salt") or ""),
        )
        _bb = resolve_brand_book(
            business_name=store_name,
            niche_id=resolved.niche_id or category,
            package_id=package_id,
            diversity_salt=str(brief.get("diversity_salt") or ""),
        )
        store_dna = apply_brand_book_to_dna(store_dna, _bb)

    # Reality Benchmark FAIL: freeze storefront HTML — Creative Identity Owner Preview
    if not should_export_marketing_html(studio_generation_status=studio.generation_status):
        identity = studio.creative_identity or invent_creative_identity(
            business_name=store_name,
            niche_id=resolved.niche_id or category,
            package_id=package_id,
            surface="store",
            diversity_salt=str(brief.get("diversity_salt") or ""),
            allow_html_export=False,
            html_blocked_reason=REALITY_BENCHMARK_NOTE,
        )
        write_creative_identity(product_dir, identity)
        write_identity_preview_as_index(product_dir, identity)
        try:
            import json as _json

            (product_dir / "html_export_gate.json").write_text(
                _json.dumps(gate_report(html_allowed=False), ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
            (product_dir / "design_dna.json").write_text(
                _json.dumps(store_dna.as_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass
        return ["index.html", "creative_identity.json", "OWNER_PREVIEW.md"]

    dna_attr_bits = " ".join(
        f'{k}="{_esc(v)}"' for k, v in store_dna.body_attrs().items()
    )
    dna_atm_html = atmosphere_html(store_dna)

    css_text = compose_store_css(resolved, package_id=package_id)
    css_text = css_text + "\n" + store_quality_floor_css(store_dna)
    (assets / "store.css").write_text(css_text, encoding="utf-8")
    (assets / "store.js").write_text(compose_store_js(ui), encoding="utf-8")
    ensure_image_slot_dirs(product_dir)

    try:
        (product_dir / "design_dna.json").write_text(
            __import__("json").dumps(store_dna.as_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass

    cats = resolved.category_labels or theme.category_labels
    products = [dict(p) for p in (resolved.demo_products or []) if isinstance(p, dict)]
    try:
        from app.factory.store_factory.store_media import seed_store_media

        seed_store_media(
            product_dir,
            category=category,
            products=products,
            package_id=package_id,
        )
    except Exception:
        # Storefront still ships; letter placeholders remain if media seed fails
        pass
    hero_line = ui["hero_suffix"].format(category=category)
    preset = resolved.visual_preset or visual_preset_for_niche(resolved.niche_id)
    _tokens, _p, pack = resolve_store_design(category, package_id=package_id)
    # Owner: premium restaurant site grade — display fonts must be visibly luxury
    try:
        from app.factory.design_dna.typography_engine import resolve_type_pair
        from app.factory.design_dna.typography_studio import resolve_type_pair_studio
        from app.factory.design_engine.fonts import FontPack

        try:
            pair = resolve_type_pair_studio(
                niche_id=resolved.niche_id or category,
                emotion=str(getattr(store_dna, "emotion", "") or ""),
                package_id=package_id,
                diversity_salt=str(brief.get("diversity_salt") or store_name),
            )
        except Exception:
            pair = resolve_type_pair(
                niche_id=resolved.niche_id or category,
                emotion=str(getattr(store_dna, "emotion", "") or "prestige"),
                package_id=package_id,
                diversity_salt=str(brief.get("diversity_salt") or store_name),
            )
        pack = FontPack(
            body=pair.body,
            display=pair.display,
            google_css_url=pair.google_css_url,
            label=pair.id,
        )
    except Exception:
        pass
    font_head = font_link_tags(pack)
    # Owner: handwritten accent (ручной шрифт) for brand + reviews
    hand_link = (
        '  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
        "family=Caveat:wght@500;600;700&display=swap\">\n"
    )
    if "Caveat" not in font_head:
        font_head = font_head + hand_link
    # Keep CSS vars in sync with the pack actually loaded
    try:
        font_override = f"""
:root {{
  --font-sans: {pack.body};
  --font-display: {pack.display};
  --font-body: {pack.body};
  --font-hand: "Caveat", "Segoe Script", "Comic Sans MS", cursive;
}}
.brand-word,
.review-card p,
.hero-eyebrow,
.card-body h3 a {{
  font-family: var(--font-hand), var(--font-display) !important;
}}
.brand-word {{ font-size: 1.35rem; font-weight: 700; }}
.review-card p {{ font-size: 1.2rem; }}
"""
        css_path = assets / "store.css"
        if css_path.is_file():
            css_path.write_text(
                css_path.read_text(encoding="utf-8") + "\n" + font_override,
                encoding="utf-8",
            )
    except Exception:
        pass

    store_director = brief.get("store_director") if isinstance(brief.get("store_director"), dict) else {}
    store_decisions = store_director.get("decisions") if isinstance(store_director, dict) else {}
    if not isinstance(store_decisions, dict):
        store_decisions = {}
    if not store_decisions:
        # Brief may omit Store Director — still apply tier decisions (Premium cinematic, etc.)
        from app.factory.visual_intelligence.store_director import decide_store_experience

        store_director = decide_store_experience(
            package_id=package_id,
            category=category,
            catalog_size=len(products),
        )
        store_decisions = dict(store_director.get("decisions") or {})
    try:
        first_n = int(store_decisions.get("first_screen_products") or 8)
    except (TypeError, ValueError):
        first_n = 8
    first_n = max(4, min(first_n, len(products) or first_n))

    # Optional studio plan for surface=store (from service)
    from app.factory.visual_intelligence.studio import convene_board
    from app.factory.visual_intelligence.studio.apply_html import apply_studio_to_html

    studio = brief.get("_studio_plan")
    if studio is None:
        try:
            studio = convene_board(
                package_id=str(
                    brief.get("package_id")
                    or (store_director or {}).get("package_id")
                    or "business"
                ),
                niche=str(brief.get("niche") or category or "generic"),
                market_code=str(brief.get("market_code") or "DE"),
                goal="commerce",
                surface="store",
                catalog_size=len(products),
                category=category,
            )
        except Exception:
            studio = None

    written: list[str] = []

    def put(name: str, content: str) -> None:
        if studio is not None:
            try:
                content = apply_studio_to_html(content, studio)
            except Exception:
                pass
        (product_dir / name).write_text(content, encoding="utf-8")
        written.append(name)

    def shell(**kwargs: Any) -> str:
        from app.factory.brand_mark import store_logo_html
        from app.factory.store_factory.templates import _is_dark_canvas

        canvas = (
            "dark"
            if _is_dark_canvas(str((resolved.colors or {}).get("background") or ""))
            else "light"
        )
        brand_html = store_logo_html(
            store_name,
            niche=resolved.niche_id or category or "",
            accent=str((resolved.colors or {}).get("accent") or "") or None,
        )
        return _shell(
            ui=ui,
            drawer=drawer,
            footer_extra=footer,
            niche_id=resolved.niche_id or "generic",
            hero_layout=preset.hero_layout,
            catalog_layout=preset.catalog_layout,
            card_preset=preset.card_preset,
            show_certs=preset.show_certs,
            font_head=font_head,
            package_id=package_id,
            dna_attrs=dna_attr_bits,
            dna_atm=dna_atm_html,
            canvas=canvas,
            brand_html=brand_html,
            **kwargs,
        )

    if "index.html" in files:
        home_products = products[:first_n] if products else []
        new_slice = home_products[: max(3, min(3, len(home_products)))] or products[:3]
        feat_slice = (
            home_products[1 : 1 + max(3, first_n // 3)] or home_products[:3] or products[:3]
        )
        best_slice = (
            home_products[2 : 2 + max(3, first_n // 3)] or home_products[:3] or products[:3]
        )
        show_recs = bool(store_decisions.get("recommendations", True))
        show_reviews_home = bool(store_decisions.get("reviews_on_home", True))
        banner = str(store_decisions.get("hero_banner") or "simple_image")
        hero_class = "hero hero-media has-hero-image"
        # Premium Store: always emotional luxury hero (Owner: branded shop, not catalog)
        if package_id == "premium" or "cinematic" in banner or "premium" in banner:
            hero_class += " hero-luxury"
        if "video" in banner:
            hero_class += " hero-video"
        recs_block = ""
        if show_recs:
            rec_label = ui.get("recommended") or ui.get("featured") or "Empfehlungen"
            recs_block = f"""
  <section class="section section-alt" id="recommendations" data-store-director="recommendations">
    <div class="wrap">
      <h2>{_esc(rec_label)}</h2>
      <div class="grid">
{_product_cards(feat_slice, ui)}
      </div>
    </div>
  </section>
"""
        reviews_block = _reviews_section(ui) if show_reviews_home else ""
        promo_title = ui.get("new_arrivals") or "Neue Kollektion"
        email = str(brief.get("email") or "").strip()
        hero_offer = _hero_offer_block(
            ui=ui,
            store_name=store_name,
            what=what,
            hero_line=hero_line,
            eyebrow=str(theme.hero_eyebrow or ""),
            cta_label=str(theme.hero_cta or ui["cta_catalog"]),
            emotional=package_id == "premium",
        )
        trust_early = _trust_bar(ui, payments=payments, shipping=shipping, email=email)
        brand_fold = ""
        if package_id == "premium":
            brand_fold = f"""
  <section class="wrap" id="brand-story" data-store-fold="brand">
    <div class="brand-story">
      <div>
        <h2>{_esc(ui.get("brand_story_title") or "Our story")}</h2>
        <p>{_esc(ui.get("brand_story_body") or what)}</p>
        <p style="margin-top:1.25rem"><a class="btn btn-ghost" href="about.html">{_esc(ui.get("about") or "About")}</a></p>
      </div>
      <div class="brand-story-media" data-image-slot="story">
        <img src="assets/images/banner.jpg" alt="" width="900" height="700" loading="lazy" decoding="async" />
      </div>
    </div>
  </section>
  <section class="wrap section" id="collections" data-store-fold="collections">
    <h2>{_esc(ui.get("collections_title") or "Collections")}</h2>
    <div class="collections-grid">
      <a class="collection-tile" href="catalog.html">
        <img src="assets/images/hero.jpg" alt="" width="600" height="400" loading="lazy" />
        <span>{_esc(ui.get("collection_1") or "Collection I")}</span>
      </a>
      <a class="collection-tile" href="catalog.html">
        <img src="assets/images/banner.jpg" alt="" width="600" height="400" loading="lazy" />
        <span>{_esc(ui.get("collection_2") or "Collection II")}</span>
      </a>
      <a class="collection-tile" href="catalog.html">
        <img src="assets/images/hero.jpg" alt="" width="600" height="400" loading="lazy" />
        <span>{_esc(ui.get("collection_3") or "Collection III")}</span>
      </a>
    </div>
  </section>
"""
            trust_early = ""
        body = f"""  <section class="{hero_class}" data-image-slot="hero" data-hero-banner="{_esc(banner)}">
    <img class="hero-photo" src="assets/images/hero.jpg" alt="{_esc(store_name)}" width="1600" height="900" decoding="async" />
{hero_offer}
  </section>
{brand_fold}{trust_early}
  <section class="wrap section" id="promo-banner" data-image-slot="banner">
    <div class="promo-banner">
      <img src="assets/images/banner.jpg" alt="" width="1600" height="600" loading="lazy" decoding="async" />
      <div class="promo-inner">
        <h2>{_esc(promo_title)}</h2>
        <p>{_esc(what)}</p>
        <p><a class="btn" href="catalog.html">{_esc(ui["cta_catalog"])}</a></p>
      </div>
    </div>
  </section>
  <section class="wrap section" id="categories">
    <h2>{_esc(ui["categories"])}</h2>
    {_category_strip(cats)}
  </section>
  <section class="section section-alt" id="featured" data-first-screen-products="{first_n}">
    <div class="wrap">
      <h2>{_esc(ui["featured"])}</h2>
      <div class="grid">
{_product_cards(feat_slice, ui)}
      </div>
    </div>
  </section>
  <section class="wrap section" id="new-arrivals">
    <h2>{_esc(ui["new_arrivals"])}</h2>
    <div class="grid">
{_product_cards(new_slice, ui)}
    </div>
  </section>
  <section class="section section-alt" id="bestsellers">
    <div class="wrap">
      <h2>{_esc(ui["bestsellers"])}</h2>
      <div class="grid">
{_product_cards(best_slice, ui)}
      </div>
    </div>
  </section>
{recs_block}{reviews_block}
  <section class="wrap section" id="why-us">
    <h2>{_esc(ui["why_us"])}</h2>
    <div class="trust">
      <div class="trust-item"><strong>{_esc(ui["secure_pay"])}</strong><span class="muted">{_esc(payments)}</span></div>
      <div class="trust-item"><strong>{_esc(ui["shipping"])}</strong><span class="muted">{_esc(shipping)}</span></div>
      <div class="trust-item"><strong>{_esc(ui["trust_returns"])}</strong><span class="muted"><a href="returns.html">{_esc(ui["trust_returns_detail"])}</a></span></div>
      <div class="trust-item"><strong>{_esc(ui["trust_contact"])}</strong><span class="muted"><a href="contact.html">{_esc(email or ui["trust_contact_detail"])}</a></span></div>
    </div>
  </section>
  <section class="section">
    <div class="newsletter">
      <h2>{_esc(ui["newsletter"])}</h2>
      <p>{_esc(ui["newsletter_body"])}</p>
      <form class="newsletter-form" onsubmit="return false;">
        <input type="email" placeholder="{_esc(ui["email_ph"])}" aria-label="{_esc(ui["email_ph"])}" />
        <button type="button" class="btn">{_esc(ui["subscribe"])}</button>
      </form>
    </div>
  </section>"""
        put(
            "index.html",
            shell(
                title=f"{store_name} | {ui['home']}",
                description=description,
                store_name=store_name,
                body=body,
            ),
        )

    if "catalog.html" in files:
        body = f"""  <div class="wrap">
    <h1 class="page-title">{_esc(ui["catalog"])}</h1>
    <p class="muted">{_esc(what)}</p>
    <div class="grid section" id="deals">
{_product_cards(products, ui)}
    </div>
  </div>"""
        put(
            "catalog.html",
            shell(
                title=f"{ui['catalog']} | {store_name}",
                description=description,
                store_name=store_name,
                body=body,
            ),
        )

    if "product.html" in files:
        sample = products[0] if products else {
            "id": "demo-1",
            "name": "Sample product",
            "price": 49.0,
            "price_label": "€49.00",
            "rating": 4.6,
            "reviews": 24,
            "stock": "In stock",
            "badge": "NEW",
        }
        pid = _esc(sample.get("id"))
        name = _esc(sample.get("name"))
        price = sample.get("price") or 0
        price_label = _esc(sample.get("price_label"))
        letter = _esc((str(sample.get("name") or "?")[:1]).upper())
        gallery_imgs: list[str] = []
        for p in [sample] + list(products[1:5]):
            if not isinstance(p, dict):
                continue
            src = str(p.get("image") or "").strip()
            if src and not src.startswith(("http://", "https://", "assets/", "/", "data:")):
                src = f"assets/images/{src.lstrip('/')}"
            if src and src not in gallery_imgs:
                gallery_imgs.append(src)
        if not gallery_imgs:
            gallery_imgs = ["assets/images/product.jpg"]
        gallery = _pdp_gallery_html(
            name=name,
            letter=letter,
            images=gallery_imgs,
            zoom_hint=ui.get("zoom_hint") or "Zoom",
        )
        related = products[1:4] if len(products) > 1 else []
        related_html = _product_cards(related, ui) if related else ""
        stock_lbl = _localize_stock(str(sample.get("stock") or "In stock"), ui)
        badge_lbl = _localize_badge(str(sample.get("badge") or ""), ui) or "Product"
        desc = (
            f"{sample.get('name')} — {what}. "
            f"{ui.get('hero_benefit_4') or ''}. "
            f"{store_name}."
        )
        body = f"""  <div class="wrap pdp" data-product-id="{pid}" data-product-name="{name}" data-product-image="{_esc(gallery_imgs[0])}" data-product-price="{price_label}">
    {gallery}
    <div class="pdp-buy">
      <p class="hero-eyebrow">{_esc(badge_lbl)}</p>
      <h1 class="page-title" style="margin-top:0">{name}</h1>
      <p class="rating">{_stars(float(sample.get('rating') or 4.5))} <span class="muted">({int(sample.get('reviews') or 0)} {_esc(ui["reviews_count"])})</span></p>
      <p class="price" style="font-size:1.6rem;margin:0.75rem 0">{price_label}</p>
      <div class="pdp-variants" aria-label="{_esc(ui["variants"])}">
        <label>{_esc(ui["size"])}
          <select aria-label="{_esc(ui["size"])}">
            <option>S</option><option selected>M</option><option>L</option><option>XL</option>
          </select>
        </label>
        <label>{_esc(ui["color"])}
          <select aria-label="{_esc(ui["color"])}">
            <option selected>Noir</option><option>Sand</option><option>Ocean</option>
          </select>
        </label>
      </div>
      <div class="btn-row pdp-cta">
        <button type="button" class="btn" data-action="add-cart" data-id="{pid}" data-name="{name}" data-price="{price}" data-price-label="{price_label}">{_esc(ui["add_cart"])}</button>
        <button type="button" class="btn btn-ghost" data-action="buy-now" data-id="{pid}" data-name="{name}" data-price="{price}" data-price-label="{price_label}">{_esc(ui["buy_now"])}</button>
        <button type="button" class="btn btn-ghost" data-action="wish" data-id="{pid}" data-name="{name}">♡ {_esc(ui["wishlist"])}</button>
      </div>
      <h2 class="pdp-subhead">{_esc(ui["description"])}</h2>
      <p class="pdp-desc">{_esc(desc)}</p>
      <h2 class="pdp-subhead">{_esc(ui["specs_title"])}</h2>
      <ul class="specs">
        <li><span>SKU</span><span>{pid}</span></li>
        <li><span>{_esc(ui["categories"])}</span><span>{_esc(category)}</span></li>
        <li><span>{_esc(ui["in_stock"])}</span><span>{_esc(stock_lbl)}</span></li>
        <li><span>{_esc(ui["shipping"])}</span><span>{_esc(shipping)}</span></li>
        <li><span>{_esc(ui["trust_returns"])}</span><span>{_esc(ui["trust_returns_detail"])}</span></li>
        <li><span>{_esc(ui["secure_pay"])}</span><span>{_esc(payments)}</span></li>
      </ul>
    </div>
  </div>
  <section class="wrap section">
    <h2>{_esc(ui["related"])}</h2>
    <div class="grid">
{related_html}
    </div>
  </section>
  <section class="wrap section" id="recently-viewed">
    <h2>{_esc(ui["recent"])}</h2>
    <div class="grid" id="recent-grid" data-recent-grid></div>
  </section>"""
        put(
            "product.html",
            shell(
                title=f"{sample.get('name')} | {store_name}",
                description=description,
                store_name=store_name,
                body=body,
            ),
        )

    if "cart.html" in files:
        body = f"""  <div class="wrap">
    <h1 class="page-title">{_esc(ui["cart_title"])}</h1>
    <p class="muted">{_esc(ui["cart_hint"])}</p>
    <div class="cart-layout">
      <div>
        <p id="cart-empty" class="muted" style="display:none">{_esc(ui["cart_empty"])} <a href="catalog.html">{_esc(ui["browse"])}</a></p>
        <div id="cart-lines"></div>
      </div>
      <aside class="cart-summary" id="cart-summary">
        <h2 style="font-size:1.15rem;margin:0 0 0.75rem">{_esc(ui["order_summary"])}</h2>
        <label for="promo">{_esc(ui["promo"])}</label>
        <input id="promo" type="text" placeholder="{_esc(ui["promo_optional"])}" />
        <p style="margin:0.75rem 0"><button type="button" class="btn btn-ghost btn-sm" id="promo-apply">{_esc(ui["apply"])}</button></p>
        <div class="total">{_esc(ui["total"])}: <span id="cart-total">€0.00</span></div>
        <button type="button" class="btn" data-action="checkout" style="width:100%">{_esc(ui["checkout"])}</button>
        <p class="muted" style="font-size:.8rem;margin-top:.75rem">{_esc(ui["checkout_note"])}</p>
      </aside>
    </div>
    <section class="wish-panel" id="wishlist">
      <h2>{_esc(ui["wish_title"])}</h2>
      <p id="wish-empty" class="muted" style="display:none">{_esc(ui["wish_empty"])} <a href="catalog.html">{_esc(ui["browse"])}</a></p>
      <div id="wish-lines"></div>
    </section>
  </div>"""
        put(
            "cart.html",
            shell(
                title=f"{ui['cart']} | {store_name}",
                description=description,
                store_name=store_name,
                body=body,
            ),
        )

    simple_pages = {
        "about.html": (
            ui["about"],
            (
                f"<p>{_esc((fabricated or {}).get('history') or '')}</p>"
                f"<p><strong>Mission:</strong> {_esc((fabricated or {}).get('mission') or what)}</p>"
                f"<p><strong>Ansatz:</strong> {_esc((fabricated or {}).get('approach') or '')}</p>"
                f"<p class='muted'>Demonstrationsunternehmen — erfunden für Virtus Core Preview.</p>"
                if fabricated
                else f"<p>{_esc(company)} — {_esc(store_name)}. {_esc(what)}.</p>"
            ),
        ),
        "contact.html": (
            ui["contact"],
            f"""<p>{_esc(company)} / {_esc(store_name)}</p>
<form>
  <label>Name</label><input type="text" name="name" />
  <label>Email</label><input type="email" name="email" />
  <label>Message</label><textarea name="message" rows="4"></textarea>
  <p style="margin-top:1rem"><button class="btn" type="button">Send</button></p>
</form>""",
        ),
        "faq.html": (
            ui["faq"],
            (
                "".join(
                    f"<p><strong>{_esc(item.get('q') if isinstance(item, dict) else '')}</strong><br/>"
                    f"{_esc(item.get('a') if isinstance(item, dict) else '')}</p>"
                    for item in (fabricated.get("faq") or [])
                )
                + "<p class='muted'>Demo-FAQ — Demonstrationsunternehmen.</p>"
                if fabricated and fabricated.get("faq")
                else f"""<p><strong>{_esc(what)}</strong></p>
<p><strong>{_esc(ui["secure_pay"])}</strong> {_esc(payments)}</p>
<p><strong>{_esc(ui["shipping"])}</strong> {_esc(shipping)}</p>"""
            ),
        ),
        "returns.html": (
            ui["returns"],
            (
                f"<p>{_esc(store_name)} — Rücksendungen innerhalb von 14 Tagen nach Erhalt. "
                "Ware unbenutzt und in Originalverpackung. "
                "Rechtliche Finalisierung vor Go-Live mit Ihrem Anwalt.</p>"
            ),
        ),
        "news.html": (ui["news"], f"<p>{_esc(store_name)}</p>"),
        "blog.html": (
            ui["blog"],
            (
                "<ul>"
                + "".join(
                    f"<li>{_esc(t)}</li>" for t in (fabricated.get("blog_titles") or [])[:6]
                )
                + "</ul><p class='muted'>Demo-Blogtitel — Demonstrationsunternehmen.</p>"
                if fabricated and fabricated.get("blog_titles")
                else f"<p>{_esc(store_name)}</p>"
            ),
        ),
        "impressum.html": (
            "Impressum",
            f"<p>{_esc(company)}</p><p>{_esc(store_name)}</p>",
        ),
        "datenschutz.html": (
            ui["privacy"],
            f"<p>{_esc(store_name)} / {_esc(company)}</p>",
        ),
    }

    for fname, (title, inner) in simple_pages.items():
        if fname not in files:
            continue
        body = f"""  <div class="wrap section">
    <h1 class="page-title">{_esc(title)}</h1>
    {inner}
  </div>"""
        put(
            fname,
            shell(
                title=f"{title} | {store_name}",
                description=description,
                store_name=store_name,
                body=body,
            ),
        )

    catalog_json = {
        "store_name": store_name,
        "products": products,
        "ui_lang": ui.get("lang"),
    }
    (assets / "catalog.json").write_text(
        json.dumps(catalog_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # R3.2 — Store Customer Account (always written; separate from Virtus identity)
    (assets / "account.js").write_text(compose_account_js(ui), encoding="utf-8")
    account_body = f"""  <div class="wrap section" id="account-app" data-account-root>
    <h1 class="page-title">{_esc(ui.get("account_title") or ui.get("account") or "Account")}</h1>
    <p class="muted">{_esc(ui.get("login") or "Sign in")} · {_esc(ui.get("register") or "Register")} — Demo-Kundenkonto (nicht Virtus Core).</p>
    <div class="header-auth" style="margin:1rem 0 1.5rem;gap:0.75rem">
      <a class="auth-login" href="#login">{_esc(ui.get("login") or "Sign in")}</a>
      <a class="auth-register" href="#register">{_esc(ui.get("register") or "Register")}</a>
    </div>
    <div id="account-panels"></div>
  </div>
  <script src="assets/account.js" defer></script>"""
    put(
        "account.html",
        shell(
            title=f"{ui.get('account_title') or 'Account'} | {store_name}",
            description=description,
            store_name=store_name,
            body=account_body,
        ),
    )

    # Checkout 1.0 — always written
    (assets / "checkout.js").write_text(compose_checkout_js(ui), encoding="utf-8")
    checkout_body = f"""  <div class="wrap section" id="checkout-app">
    <h1 class="page-title">{_esc(ui.get("checkout_title") or ui.get("checkout") or "Checkout")}</h1>
    <p class="muted">{_esc(ui.get("checkout_note") or "")}</p>
    <div id="checkout-root"></div>
  </div>
  <script src="assets/checkout.js" defer></script>"""
    put(
        "checkout.html",
        shell(
            title=f"{ui.get('checkout_title') or 'Checkout'} | {store_name}",
            description=description,
            store_name=store_name,
            body=checkout_body,
        ),
    )

    return written


def compose_checkout_js(ui: dict[str, str] | None = None) -> str:
    """Checkout 1.0 wizard — cart → auth → address → shipping → payment → place."""
    _ = ui
    return r"""/* AI Store Checkout 1.0 */
(function () {
  var TOKEN_KEY = "store_buyer_token_v1";
  var CART_KEY = "store_cart_v1";

  function cfg() {
    var s = window.__VIRTUS_STORE__ || {};
    var orderId = s.orderId || "";
    if (!orderId) {
      var m = (location.pathname || "").match(/\/stores\/([^\/]+)\/live/);
      if (m) orderId = m[1];
    }
    var apiBase = s.apiBase || (orderId ? "/api/store/" + orderId : "");
    return { orderId: orderId, apiBase: apiBase };
  }
  function token() {
    try { return localStorage.getItem(TOKEN_KEY) || ""; } catch (e) { return ""; }
  }
  function setToken(t) {
    try {
      if (t) localStorage.setItem(TOKEN_KEY, t);
      else localStorage.removeItem(TOKEN_KEY);
    } catch (e) {}
  }
  function cart() {
    try { return JSON.parse(localStorage.getItem(CART_KEY) || "[]"); } catch (e) { return []; }
  }
  function clearCart() {
    try { localStorage.setItem(CART_KEY, "[]"); } catch (e) {}
  }

  async function api(path, opts) {
    opts = opts || {};
    var c = cfg();
    var headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
    var t = token();
    if (t) headers.Authorization = "Bearer " + t;
    var res = await fetch(c.apiBase + path, {
      method: opts.method || "GET",
      headers: headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      cache: "no-store",
    });
    var body = await res.json().catch(function () { return {}; });
    if (!res.ok) {
      var err = new Error((body && (body.detail || body.message)) || "request_failed");
      err.status = res.status;
      throw err;
    }
    return body;
  }

  function field(label, name, type, value) {
    return (
      '<label style="display:block;margin:.55rem 0;font-size:.85rem">' + label +
      '<input name="' + name + '" type="' + (type || "text") + '" value="' +
      String(value == null ? "" : value).replace(/"/g, "&quot;") +
      '" style="display:block;width:100%;margin-top:.3rem;padding:.65rem .75rem;border-radius:.75rem;border:1px solid rgba(0,0,0,.12)" /></label>'
    );
  }

  var state = {
    step: "cart",
    options: null,
    address: { country: "DE" },
    shipping_method_id: "",
    payment_method_id: "",
    buyer: null,
  };

  function money(n) { return "€" + Number(n || 0).toFixed(2); }

  function cartTotal() {
    return cart().reduce(function (s, it) {
      return s + Number(it.price || 0) * Number(it.qty || 1);
    }, 0);
  }

  async function ensureOptions() {
    if (!state.options) state.options = await api("/checkout/options");
    return state.options;
  }

  async function render(root) {
    var items = cart();
    if (!items.length && state.step !== "done") {
      root.innerHTML = '<p class="muted">Cart is empty. <a href="catalog.html">Browse catalog</a></p>';
      return;
    }

    if (state.step === "cart") {
      root.innerHTML =
        '<div class="cart-summary" style="max-width:36rem">' +
        "<h2>1 · Cart</h2>" +
        items.map(function (it) {
          return "<p>" + (it.name || it.id) + " × " + (it.qty || 1) + " — " + money(it.price) + "</p>";
        }).join("") +
        "<p><strong>Subtotal: " + money(cartTotal()) + "</strong></p>" +
        '<button type="button" class="btn" id="ck-next" style="width:100%">Continue</button></div>';
      root.querySelector("#ck-next").onclick = async function () {
        if (token()) {
          try {
            var me = await api("/account/me");
            state.buyer = me.buyer;
            if (me.addresses && me.addresses[0]) state.address = Object.assign({}, me.addresses[0]);
            state.step = "address";
          } catch (e) {
            state.step = "auth";
          }
        } else state.step = "auth";
        await render(root);
      };
      return;
    }

    if (state.step === "auth") {
      root.innerHTML =
        '<div class="cart-layout"><div class="cart-summary"><h2>2 · Sign in</h2>' +
        '<form id="ck-login">' + field("Email", "email", "email") + field("Password", "password", "password") +
        '<button class="btn" type="submit" style="width:100%">Sign in</button></form></div>' +
        '<div class="cart-summary"><h2>Register</h2>' +
        '<form id="ck-reg">' + field("First name", "first_name") + field("Last name", "last_name") +
        field("Email", "email", "email") + field("Password (min 8)", "password", "password") +
        '<button class="btn" type="submit" style="width:100%">Create account</button></form></div></div>';
      async function after(body) {
        setToken(body.token);
        state.buyer = body.buyer;
        state.step = "address";
        await render(root);
      }
      root.querySelector("#ck-login").onsubmit = async function (e) {
        e.preventDefault();
        var fd = new FormData(e.target);
        try {
          await after(await api("/account/login", { method: "POST", body: { email: fd.get("email"), password: fd.get("password") } }));
        } catch (err) { alert(err.message); }
      };
      root.querySelector("#ck-reg").onsubmit = async function (e) {
        e.preventDefault();
        var fd = new FormData(e.target);
        try {
          await after(await api("/account/register", { method: "POST", body: {
            first_name: fd.get("first_name"), last_name: fd.get("last_name"),
            email: fd.get("email"), password: fd.get("password")
          }}));
        } catch (err) { alert(err.message); }
      };
      return;
    }

    if (state.step === "address") {
      var a = state.address || {};
      root.innerHTML =
        '<div class="cart-summary" style="max-width:36rem"><h2>3 · Address</h2>' +
        '<form id="ck-addr">' +
        field("Full name", "full_name", "text", a.full_name || "") +
        field("Street", "line1", "text", a.line1 || "") +
        field("City", "city", "text", a.city || "") +
        field("Postal code", "postal_code", "text", a.postal_code || "") +
        field("Country", "country", "text", a.country || "DE") +
        field("Phone", "phone", "text", a.phone || "") +
        '<button class="btn" type="submit" style="width:100%">Continue to shipping</button></form></div>';
      root.querySelector("#ck-addr").onsubmit = async function (e) {
        e.preventDefault();
        var fd = new FormData(e.target);
        state.address = {
          full_name: fd.get("full_name"), line1: fd.get("line1"), city: fd.get("city"),
          postal_code: fd.get("postal_code"), country: fd.get("country"), phone: fd.get("phone")
        };
        state.step = "shipping";
        await render(root);
      };
      return;
    }

    if (state.step === "shipping") {
      var opt = await ensureOptions();
      var methods = opt.shipping_methods || [];
      if (!methods.length) {
        root.innerHTML =
          '<div class="cart-summary" style="max-width:36rem"><h2>4 · Shipping</h2>' +
          '<p class="muted">Этот магазин пока не может отправлять товары — доставка не подключена.</p>' +
          '<button type="button" class="btn btn-ghost" id="ck-back-addr">Back</button></div>';
        root.querySelector("#ck-back-addr").onclick = async function () {
          state.step = "address";
          await render(root);
        };
        return;
      }
      root.innerHTML =
        '<div class="cart-summary" style="max-width:36rem"><h2>4 · Shipping</h2>' +
        methods.map(function (m) {
          var checked = state.shipping_method_id === m.id ? " checked" : "";
          return (
            '<label style="display:block;margin:.5rem 0;padding:.75rem;border:1px solid rgba(0,0,0,.1);border-radius:.75rem">' +
            '<input type="radio" name="ship" value="' + m.id + '"' + checked + ' /> ' +
            "<strong>" + (m.label || m.id) + "</strong> — " +
            (m.days_min || 0) + "–" + (m.days_max || 0) + " days · " + money(m.price_eur) +
            "</label>"
          );
        }).join("") +
        '<button type="button" class="btn" id="ck-ship" style="width:100%;margin-top:.75rem">Continue</button></div>';
      if (!state.shipping_method_id && methods[0]) state.shipping_method_id = methods[0].id;
      root.querySelectorAll('input[name="ship"]').forEach(function (r) {
        r.onchange = function () { state.shipping_method_id = r.value; };
      });
      root.querySelector("#ck-ship").onclick = async function () {
        if (!state.shipping_method_id) { alert("Select shipping"); return; }
        state.step = "payment";
        await render(root);
      };
      return;
    }

    if (state.step === "payment") {
      var opt2 = await ensureOptions();
      var pays = opt2.payment_methods || [];
      root.innerHTML =
        '<div class="cart-summary" style="max-width:36rem"><h2>5 · Payment</h2>' +
        '<p class="muted" style="font-size:.8rem">Checkout 1.0 stores the order — live card charge comes later.</p>' +
        pays.map(function (p) {
          var checked = state.payment_method_id === p.id ? " checked" : "";
          return (
            '<label style="display:block;margin:.5rem 0;padding:.75rem;border:1px solid rgba(0,0,0,.1);border-radius:.75rem">' +
            '<input type="radio" name="pay" value="' + p.id + '"' + checked + ' /> ' +
            "<strong>" + (p.label || p.id) + "</strong><br/><span class=\"muted\">" + (p.note || "") + "</span></label>"
          );
        }).join("") +
        '<button type="button" class="btn" id="ck-pay" style="width:100%;margin-top:.75rem">Review order</button></div>';
      if (!state.payment_method_id && pays[0]) state.payment_method_id = pays[0].id;
      root.querySelectorAll('input[name="pay"]').forEach(function (r) {
        r.onchange = function () { state.payment_method_id = r.value; };
      });
      root.querySelector("#ck-pay").onclick = async function () {
        if (!state.payment_method_id) { alert("Select payment"); return; }
        state.step = "confirm";
        await render(root);
      };
      return;
    }

    if (state.step === "confirm") {
      var opt3 = await ensureOptions();
      var ship = (opt3.shipping_methods || []).find(function (m) { return m.id === state.shipping_method_id; }) || {};
      var pay = (opt3.payment_methods || []).find(function (p) { return p.id === state.payment_method_id; }) || {};
      var sub = cartTotal();
      var shipPrice = Number(ship.price_eur || 0);
      if (opt3.free_shipping_from_eur != null && sub >= Number(opt3.free_shipping_from_eur)) shipPrice = 0;
      root.innerHTML =
        '<div class="cart-summary" style="max-width:36rem"><h2>6 · Confirm</h2>' +
        "<p>Items: " + money(sub) + "</p>" +
        "<p>Shipping (" + (ship.label || "") + "): " + money(shipPrice) + "</p>" +
        "<p>Payment: " + (pay.label || "") + "</p>" +
        "<p><strong>Total: " + money(sub + shipPrice) + "</strong></p>" +
        '<button type="button" class="btn" id="ck-place" style="width:100%">Place order</button>' +
        '<p id="ck-msg" class="muted"></p></div>';
      root.querySelector("#ck-place").onclick = async function () {
        var btn = root.querySelector("#ck-place");
        btn.disabled = true;
        try {
          var out = await api("/checkout/place", {
            method: "POST",
            body: {
              items: cart(),
              address: state.address,
              shipping_method_id: state.shipping_method_id,
              payment_method_id: state.payment_method_id,
              save_address: true,
            },
          });
          clearCart();
          state.step = "done";
          state.lastOrder = out.order;
          state.lastEmail = out.email;
          await render(root);
        } catch (err) {
          btn.disabled = false;
          root.querySelector("#ck-msg").textContent = err.message || "Failed";
        }
      };
      return;
    }

    if (state.step === "done") {
      var o = state.lastOrder || {};
      root.innerHTML =
        '<div class="cart-summary" style="max-width:36rem"><h2>Order placed</h2>' +
        "<p><strong>" + (o.id || "") + "</strong></p>" +
        "<p>Status: " + (o.status || "") + " · Total " + money(o.total_eur) + "</p>" +
        '<p class="muted">Confirmation queued' +
        (state.lastEmail && state.lastEmail.delivery ? " (" + state.lastEmail.delivery + ")" : "") +
        ".</p>" +
        '<p><a class="btn" href="account.html#orders">Open my orders</a> ' +
        '<a class="btn btn-ghost" href="catalog.html">Continue shopping</a></p></div>';
    }
  }

  async function boot() {
    var root = document.getElementById("checkout-root");
    if (!root) return;
    if (!cfg().orderId) {
      root.innerHTML = '<p class="muted">Open checkout via the live shop URL.</p>';
      return;
    }
    await render(root);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
"""


def compose_account_js(ui: dict[str, str] | None = None) -> str:
    """Store buyer account UI — talks to /api/store/{{orderId}}/account/*."""
    u = ui or {}
    login = str(u.get("login") or "Sign in")
    register = str(u.get("register") or "Register")
    js = r"""/* AI Store R3.2 — Store Customer Account */
(function () {
  var TOKEN_KEY = "store_buyer_token_v1";
  var WISH_KEY = "store_wish_v1";
  var L = { login: "__LOGIN__", register: "__REGISTER__" };

  function cfg() {
    var s = window.__VIRTUS_STORE__ || {};
    var orderId = s.orderId || "";
    if (!orderId) {
      var m = (location.pathname || "").match(/\/stores\/([^\/]+)\/live/);
      if (m) orderId = m[1];
    }
    var apiBase = s.apiBase || (orderId ? "/api/store/" + orderId : "");
    return { orderId: orderId, apiBase: apiBase };
  }

  function token() {
    try { return localStorage.getItem(TOKEN_KEY) || ""; } catch (e) { return ""; }
  }
  function setToken(t) {
    try {
      if (t) localStorage.setItem(TOKEN_KEY, t);
      else localStorage.removeItem(TOKEN_KEY);
    } catch (e) {}
  }

  async function api(path, opts) {
    opts = opts || {};
    var c = cfg();
    var headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
    var t = token();
    if (t) headers.Authorization = "Bearer " + t;
    var res = await fetch(c.apiBase + "/account" + path, {
      method: opts.method || "GET",
      headers: headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      cache: "no-store",
    });
    var body = await res.json().catch(function () { return {}; });
    if (!res.ok) {
      var err = new Error((body && body.detail) || "request_failed");
      err.status = res.status;
      err.body = body;
      throw err;
    }
    return body;
  }

  function el(html) {
    var d = document.createElement("div");
    d.innerHTML = html.trim();
    return d.firstChild;
  }

  function field(label, name, type, value) {
    type = type || "text";
    value = value == null ? "" : value;
    return (
      '<label style="display:block;margin:.6rem 0;font-size:.85rem">' +
      label +
      '<input name="' + name + '" type="' + type + '" value="' + String(value).replace(/"/g, "&quot;") +
      '" style="display:block;width:100%;margin-top:.35rem;padding:.65rem .75rem;border-radius:.75rem;border:1px solid rgba(0,0,0,.12)" />' +
      "</label>"
    );
  }

  function renderAuth(root) {
    root.innerHTML =
      '<div class="cart-layout" style="margin-top:1rem">' +
      '<div class="cart-summary" id="login"><h2 style="margin-top:0">__LOGIN__</h2>' +
      '<form id="login-form">' +
      field("Email", "email", "email") +
      field("Password", "password", "password") +
      '<button class="btn" type="submit" style="width:100%;margin-top:.5rem">__LOGIN__</button>' +
      '</form><p class="muted" style="font-size:.8rem;margin-top:1rem"><a href="#forgot" id="goto-forgot">Forgot password?</a></p></div>' +
      '<div class="cart-summary" id="register"><h2 style="margin-top:0">__REGISTER__</h2>' +
      '<form id="reg-form">' +
      field("First name", "first_name") +
      field("Last name", "last_name") +
      field("Email", "email", "email") +
      field("Password (min 8)", "password", "password") +
      '<button class="btn" type="submit" style="width:100%;margin-top:.5rem">__REGISTER__</button>' +
      "</form></div></div>" +
      '<div id="forgot-box" style="display:none;margin-top:1rem" class="cart-summary">' +
      "<h2>Reset password</h2>" +
      '<form id="forgot-form">' +
      field("Email", "email", "email") +
      '<button class="btn btn-ghost" type="submit">Request reset</button></form>' +
      '<form id="reset-form" style="margin-top:1rem">' +
      field("Email", "email", "email") +
      field("Reset token", "token") +
      field("New password", "password", "password") +
      '<button class="btn" type="submit">Set new password</button></form>' +
      '<p id="auth-msg" class="muted"></p></div>';

    root.querySelector("#goto-forgot").onclick = function (e) {
      e.preventDefault();
      root.querySelector("#forgot-box").style.display = "block";
    };

    async function afterAuth(body) {
      setToken(body.token);
      try {
        var localWish = JSON.parse(localStorage.getItem(WISH_KEY) || "[]");
        if (localWish && localWish.length) {
          await api("/wishlist", {
            method: "PUT",
            body: {
              items: localWish.map(function (w) {
                return {
                  product_id: w.id || w.product_id,
                  title: w.name || w.title,
                  price: w.price,
                  image: w.image,
                };
              }),
            },
          });
        }
      } catch (e) {}
      await renderCabinet(root);
    }

    root.querySelector("#login-form").onsubmit = async function (e) {
      e.preventDefault();
      var fd = new FormData(e.target);
      try {
        var body = await api("/login", {
          method: "POST",
          body: { email: fd.get("email"), password: fd.get("password") },
        });
        await afterAuth(body);
      } catch (err) {
        alert(err.message || "Login failed");
      }
    };
    root.querySelector("#reg-form").onsubmit = async function (e) {
      e.preventDefault();
      var fd = new FormData(e.target);
      try {
        var body = await api("/register", {
          method: "POST",
          body: {
            first_name: fd.get("first_name"),
            last_name: fd.get("last_name"),
            email: fd.get("email"),
            password: fd.get("password"),
          },
        });
        await afterAuth(body);
      } catch (err) {
        alert(err.message || "Register failed");
      }
    };
    root.querySelector("#forgot-form").onsubmit = async function (e) {
      e.preventDefault();
      var fd = new FormData(e.target);
      try {
        var body = await api("/forgot-password", {
          method: "POST",
          body: { email: fd.get("email") },
        });
        var msg = body.message || "OK";
        if (body.dev_reset_token) {
          msg += " · token: " + body.dev_reset_token;
          var rt = root.querySelector('#reset-form input[name="token"]');
          var re = root.querySelector('#reset-form input[name="email"]');
          if (rt) rt.value = body.dev_reset_token;
          if (re) re.value = fd.get("email");
        }
        root.querySelector("#auth-msg").textContent = msg;
      } catch (err) {
        alert(err.message || "Failed");
      }
    };
    root.querySelector("#reset-form").onsubmit = async function (e) {
      e.preventDefault();
      var fd = new FormData(e.target);
      try {
        var body = await api("/reset-password", {
          method: "POST",
          body: {
            email: fd.get("email"),
            token: fd.get("token"),
            password: fd.get("password"),
          },
        });
        await afterAuth(body);
      } catch (err) {
        alert(err.message || "Reset failed");
      }
    };
  }

  async function renderCabinet(root) {
    var me;
    try {
      me = await api("/me");
    } catch (err) {
      setToken("");
      renderAuth(root);
      return;
    }
    var b = me.buyer || {};
    var addrs = me.addresses || [];
    var wish = me.wishlist || [];
    var orders = me.orders || [];

    root.innerHTML =
      '<div style="display:flex;flex-wrap:wrap;gap:.5rem;margin:1rem 0">' +
      '<button type="button" class="btn btn-sm" data-tab="profile">Profile</button>' +
      '<button type="button" class="btn btn-ghost btn-sm" data-tab="addresses">Addresses</button>' +
      '<button type="button" class="btn btn-ghost btn-sm" data-tab="wishlist">Wishlist</button>' +
      '<button type="button" class="btn btn-ghost btn-sm" data-tab="orders">Orders</button>' +
      '<button type="button" class="btn btn-ghost btn-sm" id="logout-btn">Sign out</button>' +
      '</div><div id="tab-body"></div>';

    function show(tab) {
      var box = root.querySelector("#tab-body");
      if (tab === "profile") {
        box.innerHTML =
          '<form id="profile-form" class="cart-summary" style="max-width:28rem">' +
          field("First name", "first_name", "text", b.first_name) +
          field("Last name", "last_name", "text", b.last_name) +
          field("Phone", "phone", "text", b.phone) +
          field("New password (optional)", "password", "password", "") +
          '<p class="muted" style="font-size:.8rem">Email: ' +
          (b.email || "") +
          " (login)</p>" +
          '<button class="btn" type="submit">Save profile</button></form>';
        box.querySelector("#profile-form").onsubmit = async function (e) {
          e.preventDefault();
          var fd = new FormData(e.target);
          var payload = {
            first_name: fd.get("first_name"),
            last_name: fd.get("last_name"),
            phone: fd.get("phone"),
          };
          if (fd.get("password")) payload.password = fd.get("password");
          try {
            var out = await api("/me", { method: "PATCH", body: payload });
            b = out.buyer || b;
            alert("Saved");
          } catch (err) {
            alert(err.message || "Save failed");
          }
        };
      } else if (tab === "addresses") {
        var list = addrs
          .map(function (a) {
            return (
              '<div class="wish-line"><div><strong>' +
              (a.label || "Address") +
              "</strong><br/>" +
              (a.full_name || "") +
              "<br/>" +
              (a.line1 || "") +
              ", " +
              (a.postal_code || "") +
              " " +
              (a.city || "") +
              " (" +
              (a.country || "") +
              ')</div><button type="button" class="btn btn-ghost btn-sm" data-del-addr="' +
              a.id +
              '">Remove</button></div>'
            );
          })
          .join("");
        box.innerHTML =
          (list || '<p class="muted">No addresses yet.</p>') +
          '<form id="addr-form" class="cart-summary" style="margin-top:1rem;max-width:28rem">' +
          "<h3>Add address</h3>" +
          field("Label", "label", "text", "Home") +
          field("Full name", "full_name") +
          field("Street", "line1") +
          field("City", "city") +
          field("Postal code", "postal_code") +
          field("Country", "country", "text", "DE") +
          '<button class="btn" type="submit">Save address</button></form>';
        box.querySelectorAll("[data-del-addr]").forEach(function (btn) {
          btn.onclick = async function () {
            try {
              var out = await api("/addresses/" + btn.getAttribute("data-del-addr"), {
                method: "DELETE",
              });
              addrs = out.addresses || [];
              show("addresses");
            } catch (err) {
              alert(err.message || "Failed");
            }
          };
        });
        box.querySelector("#addr-form").onsubmit = async function (e) {
          e.preventDefault();
          var fd = new FormData(e.target);
          try {
            var out = await api("/addresses", {
              method: "POST",
              body: {
                label: fd.get("label"),
                full_name: fd.get("full_name"),
                line1: fd.get("line1"),
                city: fd.get("city"),
                postal_code: fd.get("postal_code"),
                country: fd.get("country"),
                is_default: true,
              },
            });
            addrs = out.addresses || [];
            show("addresses");
          } catch (err) {
            alert(err.message || "Failed");
          }
        };
      } else if (tab === "wishlist") {
        box.innerHTML =
          wish.length === 0
            ? '<p class="muted">Wishlist is empty. Save items while browsing, then sign in to sync.</p>'
            : wish
                .map(function (w) {
                  return (
                    '<div class="wish-line"><div><strong>' +
                    (w.title || w.product_id) +
                    "</strong><br/>€" +
                    Number(w.price || 0).toFixed(2) +
                    "</div></div>"
                  );
                })
                .join("");
      } else {
        box.innerHTML =
          '<p class="muted">Order history will appear here after Commerce (R3.3).</p>' +
          (orders.length
            ? "<pre>" + JSON.stringify(orders, null, 2) + "</pre>"
            : "<p>No orders yet.</p>");
      }
    }

    root.querySelectorAll("[data-tab]").forEach(function (btn) {
      btn.onclick = function () {
        show(btn.getAttribute("data-tab"));
      };
    });
    root.querySelector("#logout-btn").onclick = function () {
      setToken("");
      renderAuth(root);
    };
    show("profile");
  }

  async function boot() {
    var root = document.getElementById("account-panels");
    if (!root) return;
    if (!cfg().orderId) {
      root.innerHTML =
        '<p class="muted">Open this page via the live shop URL so your store id is known.</p>';
      return;
    }
    if (token()) await renderCabinet(root);
    else {
      renderAuth(root);
      var h = (location.hash || '').toLowerCase();
      if (h.indexOf('register') >= 0) {
        var r = document.getElementById('register');
        if (r) r.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } else if (h.indexOf('login') >= 0) {
        var l = document.getElementById('login');
        if (l) l.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
"""
    return (
        js.replace("__LOGIN__", login).replace("__REGISTER__", register)
    )
