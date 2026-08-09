"""Shop quality gate — navigation, required pages, title/description, theme colors, R2.1 commerce UX."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.factory.store_factory.composer import pages_for_brief

_PURE_WHITE = re.compile(
    r"--store-bg\s*:\s*(#fff(?:fff)?|white)\s*;",
    re.I,
)


@dataclass
class QualityResult:
    passed: bool
    checks: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": self.checks,
            "errors": self.errors,
        }


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


def run_shop_quality_gate(
    product_dir: Path,
    *,
    brief: dict[str, Any],
    colors: dict[str, str] | None = None,
) -> QualityResult:
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    required = pages_for_brief(brief)
    missing = [f for f in required if not (product_dir / f).is_file()]
    ok_pages = len(missing) == 0
    checks.append(
        _check(
            "required_pages",
            ok_pages,
            "ok" if ok_pages else f"missing: {', '.join(missing)}",
        )
    )
    if not ok_pages:
        errors.append(f"missing_pages:{','.join(missing)}")

    index = product_dir / "index.html"
    html = ""
    if index.is_file():
        html = index.read_text(encoding="utf-8")

    store_name = str(brief.get("store_name") or "")
    has_title = bool(re.search(r"<title>[^<]+</title>", html, re.I))
    title_has_name = store_name.lower() in html.lower() if store_name else False
    checks.append(_check("title_present", has_title))
    checks.append(
        _check("store_name_in_html", title_has_name, store_name or "(empty)")
    )
    if not has_title:
        errors.append("missing_title")
    if store_name and not title_has_name:
        errors.append("store_name_missing")

    has_desc = 'name="description"' in html.lower()
    checks.append(_check("meta_description", has_desc))
    if not has_desc:
        errors.append("missing_description")

    has_nav = (
        'id="nav-drawer"' in html
        or 'aria-label="Main"' in html
        or 'class="nav"' in html
    )
    checks.append(_check("navigation", has_nav))
    if not has_nav:
        errors.append("missing_nav")

    css_path = product_dir / "assets" / "store.css"
    css = css_path.read_text(encoding="utf-8") if css_path.is_file() else ""
    accent = (colors or {}).get("accent") or ""
    colors_ok = bool(css) and (
        "--store-accent" in css and (not accent or accent.lower() in css.lower())
    )
    checks.append(_check("colors_applied", colors_ok, accent or "theme"))
    if not colors_ok:
        errors.append("colors_not_applied")

    warm_ok = bool(css) and "--store-bg" in css and not _PURE_WHITE.search(css)
    checks.append(_check("warm_background", warm_ok, "non-white --store-bg"))
    if not warm_ok:
        errors.append("flat_white_background")

    js_path = product_dir / "assets" / "store.js"
    js_ok = js_path.is_file() and "store_cart_v1" in js_path.read_text(encoding="utf-8")
    checks.append(_check("store_js_cart", js_ok))
    if not js_ok:
        errors.append("missing_store_js")

    cart_page = product_dir / "cart.html"
    cart_html = cart_page.read_text(encoding="utf-8") if cart_page.is_file() else ""
    cart_ok = bool(cart_html) and "cart-lines" in cart_html and "wish-lines" in cart_html
    checks.append(_check("cart_page", cart_ok))
    if not cart_ok:
        errors.append("missing_cart_page")

    catalog = product_dir / "catalog.html"
    catalog_html = catalog.read_text(encoding="utf-8") if catalog.is_file() else ""
    catalog_ok = bool(catalog_html) and 'class="card"' in catalog_html
    checks.append(_check("demo_catalog_cards", catalog_ok))
    if not catalog_ok:
        errors.append("demo_catalog_missing")

    wish_link_ok = 'href="cart.html#wishlist"' in html or 'href="cart.html#wishlist"' in catalog_html
    checks.append(_check("wishlist_nav", wish_link_ok))
    if not wish_link_ok:
        errors.append("missing_wishlist_nav")

    mobile_ok = 'class="mobile-bar"' in html or 'class="mobile-bar"' in catalog_html
    checks.append(_check("mobile_bar", mobile_ok))
    if not mobile_ok:
        errors.append("missing_mobile_bar")

    no_fake_wish = 'data-id="header"' not in html and 'data-id="header"' not in catalog_html
    checks.append(_check("no_fake_header_wish", no_fake_wish))
    if not no_fake_wish:
        errors.append("fake_header_wish")

    commerce_ok = (
        'data-action="add-cart"' in catalog_html
        or 'data-action="add-cart"' in html
    ) and ("data-cart-badge" in html or "data-cart-badge" in catalog_html)
    checks.append(_check("commerce_cta", commerce_ok, "Add to Cart + cart badge"))
    if not commerce_ok:
        errors.append("missing_commerce_cta")

    brand_home = 'class="brand" href="index.html"' in html or 'class="brand" href="index.html"' in catalog_html
    checks.append(_check("logo_home", brand_home or 'href="index.html"' in html))
    if not (brand_home or 'class="brand"' in html):
        errors.append("missing_logo_home")

    # Visual Intelligence Engine markers
    vie_ok = 'data-vie-engine=' in html
    checks.append(_check("visual_intelligence", vie_ok, "data-vie-engine on store shell"))
    if not vie_ok:
        errors.append("missing_visual_intelligence")

    passed = len(errors) == 0
    return QualityResult(passed=passed, checks=checks, errors=errors)
