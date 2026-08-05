"""Compose static HTML pages from shop_brief + resolved template (AI Store R2.1)."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

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


def ui_copy(brief: dict[str, Any]) -> dict[str, str]:
    """Storefront chrome strings — DE-first for DACH, else English."""
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
            "account": "Konto",
            "account_title": "Mein Konto",
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
                "Die Kasse wird aktiv, sobald der Händler Zahlungen freischaltet. "
                "Dieses Demo speichert den Warenkorb nur lokal — keine Abbuchung."
            ),
            "toast_added": "Zum Warenkorb hinzugefügt",
            "toast_wish_add": "Auf die Merkliste",
            "toast_wish_rm": "Von der Merkliste entfernt",
            "toast_checkout": "Demo-Kasse — Zahlungen folgen später",
            "toast_promo": "Gutscheine aktivieren sich mit der Live-Kasse",
            "remove": "Entfernen",
            "in_stock": "Auf Lager",
            "few_left": "Nur noch wenige",
            "related": "Das könnte Ihnen auch gefallen",
            "reviews_count": "Bewertungen",
            "hero_suffix": "Kuratiert für {category} — modernes Einkaufen mit Premium-Gefühl.",
            "badge_new": "NEU",
            "badge_sale": "SALE",
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
        "account": "Account",
        "account_title": "My account",
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
            "Checkout connects when the merchant enables payments. "
            "This demo keeps your cart in localStorage only — no charge."
        ),
        "toast_added": "Added to cart",
        "toast_wish_add": "Saved to wishlist",
        "toast_wish_rm": "Removed from wishlist",
        "toast_checkout": "Demo checkout — payments connect later",
        "toast_promo": "Promo codes activate when checkout is live",
        "remove": "Remove",
        "in_stock": "In stock",
        "few_left": "Few left",
        "related": "You may also like",
        "reviews_count": "reviews",
        "hero_suffix": "Curated for {category} — crafted for everyday premium shopping.",
        "badge_new": "NEW",
        "badge_sale": "SALE",
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


def compose_store_css(resolved: ResolvedTemplate) -> str:
    c = resolved.colors
    return f"""/* AI Store R2.1 — premium storefront */
@import url("https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&display=swap");

:root {{
  --store-primary: {c['primary']};
  --store-secondary: {c['secondary']};
  --store-accent: {c['accent']};
  --store-bg: {c['background']};
  --store-surface: {c['surface']};
  --store-text: {c['text']};
  --store-muted: {c['muted']};
  --store-radius: 1rem;
  --store-shadow: 0 10px 40px rgba(28, 25, 23, 0.08);
  --store-shadow-hover: 0 18px 48px rgba(28, 25, 23, 0.14);
  --font-sans: "DM Sans", "Segoe UI", system-ui, sans-serif;
  --font-display: "Fraunces", Georgia, serif;
}}

* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  font-family: var(--font-sans);
  color: var(--store-text);
  line-height: 1.55;
  min-height: 100vh;
  background:
    radial-gradient(ellipse 80% 50% at 10% -10%, color-mix(in srgb, var(--store-accent) 18%, transparent), transparent 55%),
    radial-gradient(ellipse 60% 40% at 90% 5%, color-mix(in srgb, var(--store-secondary) 80%, transparent), transparent 50%),
    linear-gradient(180deg, var(--store-bg) 0%, color-mix(in srgb, var(--store-secondary) 45%, var(--store-bg)) 45%, var(--store-bg) 100%);
  background-attachment: fixed;
}}
body::before {{
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(circle at 20% 70%, color-mix(in srgb, var(--store-accent) 8%, transparent), transparent 35%),
    radial-gradient(circle at 85% 55%, color-mix(in srgb, var(--store-primary) 6%, transparent), transparent 40%);
  filter: blur(40px);
  opacity: 0.9;
}}
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
.nav-drawer a {{
  display: block;
  padding: 0.75rem 0.9rem;
  border-radius: 0.75rem;
  color: var(--store-text);
  font-weight: 500;
  transition: background 0.2s ease, transform 0.2s ease;
}}
.nav-drawer a:hover {{
  background: color-mix(in srgb, var(--store-secondary) 70%, transparent);
  text-decoration: none;
  transform: translateX(4px);
}}
.drawer-close {{ align-self: flex-end; }}

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
  gap: 0.65rem;
}}
.cat-chip {{
  display: inline-flex;
  padding: 0.55rem 1rem;
  border-radius: 999px;
  background: var(--store-surface);
  border: 1px solid color-mix(in srgb, var(--store-secondary) 80%, transparent);
  color: var(--store-text);
  font-weight: 500;
  font-size: 0.9rem;
  box-shadow: 0 4px 16px rgba(28,25,23,0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
.cat-chip:hover {{
  transform: translateY(-2px);
  box-shadow: var(--store-shadow);
  text-decoration: none;
}}

.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1.25rem;
}}
.card {{
  background: var(--store-surface);
  border: 1px solid color-mix(in srgb, var(--store-secondary) 75%, transparent);
  border-radius: var(--store-radius);
  padding: 0;
  overflow: hidden;
  box-shadow: var(--store-shadow);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  display: flex;
  flex-direction: column;
  position: relative;
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
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 600;
  color: color-mix(in srgb, var(--store-primary) 45%, transparent);
  position: relative;
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
.review-card {{
  background: var(--store-surface);
  border-radius: var(--store-radius);
  padding: 1.35rem 1.25rem;
  box-shadow: var(--store-shadow);
  border: 1px solid color-mix(in srgb, var(--store-secondary) 70%, transparent);
}}
.review-card .rating {{ margin: 0 0 0.65rem; }}
.review-card p {{ margin: 0 0 0.85rem; color: var(--store-text); font-size: 0.95rem; }}
.review-card cite {{
  font-style: normal;
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--store-muted);
}}

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
.newsletter .btn {{ background: #fff; color: var(--store-primary); box-shadow: none; }}

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
        var note = document.getElementById("checkout-note");
        if (note) note.classList.add("show");
        toast(UI.toastCheckout);
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
}})();
"""


def _drawer_links(files: list[str], ui: dict[str, str]) -> str:
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
    order = [
        "index.html",
        "catalog.html",
        "cart.html",
        "about.html",
        "contact.html",
        "faq.html",
        "returns.html",
        "impressum.html",
        "datenschutz.html",
        "news.html",
        "blog.html",
    ]
    parts = []
    file_set = set(files)
    for f in order:
        if f not in file_set and f != "index.html":
            continue
        if f == "index.html" or f in file_set:
            label = labels.get(f, f.replace(".html", "").title())
            href = f
            if f == "catalog.html":
                parts.append(f'<a href="{_esc(href)}">{_esc(label)}</a>')
                parts.append(f'<a href="catalog.html#deals">{_esc(ui["deals"])}</a>')
            else:
                parts.append(f'<a href="{_esc(href)}">{_esc(label)}</a>')
    parts.append(f'<a href="cart.html#wishlist">{_esc(ui["wishlist"])}</a>')
    parts.append(f'<a href="account.html">{_esc(ui.get("account") or "Account")}</a>')
    return "\n      ".join(parts)


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
) -> str:
    lang = ui.get("lang") or "en"
    return f"""<!DOCTYPE html>
<html lang="{_esc(lang)}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_esc(title)}</title>
  <meta name="description" content="{_esc(description)}" />
  <link rel="stylesheet" href="assets/store.css" />
</head>
<body>
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
      <a class="brand" href="index.html">{_esc(store_name)}</a>
      <div class="header-search">
        <input id="header-search" type="search" placeholder="{_esc(ui["search_ph"])}" aria-label="{_esc(ui["search_ph"])}" />
      </div>
      <div class="header-actions">
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
            cls = "badge sale" if str(p.get("badge") or "").upper() == "SALE" else "badge"
            badge_html = f'<span class="{cls}">{_esc(badge)}</span>'
        rating = float(p.get("rating") or 4.5)
        reviews = int(p.get("reviews") or 0)
        stock = _localize_stock(str(p.get("stock") or "In stock"), ui)
        stock_cls = "stock low" if "few" in stock.lower() or "wenig" in stock.lower() else "stock"
        letter = _esc((str(p.get("name") or "?")[:1]).upper())
        old_html = f'<span class="old-price">{old}</span>' if old else ""
        bits.append(
            f"""    <article class="card" data-product-card data-name="{name}" data-id="{pid}">
      {badge_html}
      <button type="button" class="wish-btn" data-action="wish" data-id="{pid}" data-name="{name}" aria-label="{_esc(ui["wishlist"])}">♡</button>
      <a href="product.html?id={pid}" class="card-media" aria-hidden="true">{letter}</a>
      <div class="card-body">
        <h3><a href="product.html?id={pid}">{name}</a></h3>
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
    (assets / "store.css").write_text(compose_store_css(resolved), encoding="utf-8")
    (assets / "store.js").write_text(compose_store_js(ui), encoding="utf-8")

    cats = resolved.category_labels or theme.category_labels
    products = resolved.demo_products
    hero_line = ui["hero_suffix"].format(category=category)

    written: list[str] = []

    def put(name: str, content: str) -> None:
        (product_dir / name).write_text(content, encoding="utf-8")
        written.append(name)

    def shell(**kwargs: Any) -> str:
        return _shell(ui=ui, drawer=drawer, footer_extra=footer, **kwargs)

    if "index.html" in files:
        new_slice = products[:3]
        feat_slice = products[1:4] if len(products) > 3 else products
        best_slice = products[2:5] if len(products) > 4 else products
        body = f"""  <section class="hero">
    <div class="wrap">
      <p class="hero-eyebrow">{_esc(theme.hero_eyebrow)}</p>
      <h1>{_esc(store_name)}</h1>
      <p>{_esc(what)}. {_esc(hero_line)}</p>
      <a class="btn" href="catalog.html">{_esc(theme.hero_cta)}</a>
    </div>
  </section>
  <section class="wrap section" id="categories">
    <h2>{_esc(ui["categories"])}</h2>
    {_category_strip(cats)}
  </section>
  <section class="section section-alt" id="featured">
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
{_reviews_section(ui)}
  <section class="wrap section">
    <h2>{_esc(ui["why_us"])}</h2>
    <div class="trust">
      <div class="trust-item"><strong>{_esc(ui["secure_pay"])}</strong><span class="muted">{_esc(payments)}</span></div>
      <div class="trust-item"><strong>{_esc(ui["shipping"])}</strong><span class="muted">{_esc(shipping)}</span></div>
      <div class="trust-item"><strong>{_esc(ui["niche"])}</strong><span class="muted">{_esc(category)}</span></div>
      <div class="trust-item"><strong>{_esc(ui["care"])}</strong><span class="muted">{_esc(ui["care_detail"])}</span></div>
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
        related = products[1:4] if len(products) > 1 else []
        related_html = _product_cards(related, ui) if related else ""
        stock_lbl = _localize_stock(str(sample.get("stock") or "In stock"), ui)
        badge_lbl = _localize_badge(str(sample.get("badge") or ""), ui) or "Product"
        body = f"""  <div class="wrap pdp">
    <div class="pdp-gallery" aria-label="Product gallery">{letter}</div>
    <div>
      <p class="hero-eyebrow">{_esc(badge_lbl)}</p>
      <h1 class="page-title" style="margin-top:0">{name}</h1>
      <p class="rating">{_stars(float(sample.get('rating') or 4.5))} <span class="muted">({int(sample.get('reviews') or 0)} {_esc(ui["reviews_count"])})</span></p>
      <p class="price" style="font-size:1.6rem;margin:0.75rem 0">{price_label}</p>
      <p class="muted">{_esc(store_name)}. {_esc(what)}.</p>
      <ul class="specs">
        <li><span>SKU</span><span>{pid}</span></li>
        <li><span>{_esc(ui["categories"])}</span><span>{_esc(category)}</span></li>
        <li><span>{_esc(ui["in_stock"])}</span><span>{_esc(stock_lbl)}</span></li>
        <li><span>{_esc(ui["shipping"])}</span><span>{_esc(shipping)}</span></li>
      </ul>
      <div class="btn-row">
        <button type="button" class="btn" data-action="add-cart" data-id="{pid}" data-name="{name}" data-price="{price}" data-price-label="{price_label}">{_esc(ui["add_cart"])}</button>
        <button type="button" class="btn btn-ghost" data-action="buy-now" data-id="{pid}" data-name="{name}" data-price="{price}" data-price-label="{price_label}">{_esc(ui["buy_now"])}</button>
        <button type="button" class="btn btn-ghost" data-action="wish" data-id="{pid}" data-name="{name}">♡ {_esc(ui["wishlist"])}</button>
      </div>
    </div>
  </div>
  <section class="wrap section">
    <h2>{_esc(ui["related"])}</h2>
    <div class="grid">
{related_html}
    </div>
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
        <p class="checkout-note" id="checkout-note">{_esc(ui["checkout_note"])}</p>
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
            f"<p>{_esc(company)} — {_esc(store_name)}. {_esc(what)}.</p>",
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
            f"""<p><strong>{_esc(what)}</strong></p>
<p><strong>{_esc(ui["secure_pay"])}</strong> {_esc(payments)}</p>
<p><strong>{_esc(ui["shipping"])}</strong> {_esc(shipping)}</p>""",
        ),
        "returns.html": (
            ui["returns"],
            "<p>Returns policy placeholder — finalize with your legal counsel before go-live.</p>",
        ),
        "news.html": (ui["news"], f"<p>{_esc(store_name)}</p>"),
        "blog.html": (ui["blog"], f"<p>{_esc(store_name)}</p>"),
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
    <p class="muted">Shop customer account — not Virtus Core login.</p>
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

    return written


def compose_account_js(ui: dict[str, str] | None = None) -> str:
    """Store buyer account UI — talks to /api/store/{{orderId}}/account/*."""
    _ = ui  # reserved for i18n expansion
    return r"""/* AI Store R3.2 — Store Customer Account */
(function () {
  var TOKEN_KEY = "store_buyer_token_v1";
  var WISH_KEY = "store_wish_v1";

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
      '<div class="cart-summary"><h2 style="margin-top:0">Sign in</h2>' +
      '<form id="login-form">' +
      field("Email", "email", "email") +
      field("Password", "password", "password") +
      '<button class="btn" type="submit" style="width:100%;margin-top:.5rem">Sign in</button>' +
      '</form><p class="muted" style="font-size:.8rem;margin-top:1rem"><a href="#forgot" id="goto-forgot">Forgot password?</a></p></div>' +
      '<div class="cart-summary"><h2 style="margin-top:0">Create account</h2>' +
      '<form id="reg-form">' +
      field("First name", "first_name") +
      field("Last name", "last_name") +
      field("Email", "email", "email") +
      field("Password (min 8)", "password", "password") +
      '<button class="btn" type="submit" style="width:100%;margin-top:.5rem">Register</button>' +
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
    else renderAuth(root);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
"""
