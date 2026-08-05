"""Apply owner Design overlay onto Factory HTML (User Data Protection)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from app.integration.store_admin.design_service import FONT_PRESETS, StoreDesignService


def _font_preset(preset_id: str) -> dict[str, str]:
    for row in FONT_PRESETS:
        if row["id"] == preset_id:
            return row
    return FONT_PRESETS[0]


def _copy_owner_asset(
    memory_dir: Path,
    order_id: str,
    img: dict[str, Any] | None,
    dest_dir: Path,
    filename: str,
) -> str | None:
    """Copy design media into storefront assets; return relative URL or None."""
    if not isinstance(img, dict) or not img.get("path"):
        return None
    try:
        svc = StoreDesignService(memory_dir)
        src = svc._media.resolve_path(str(img["path"]))  # noqa: SLF001
    except Exception:
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext = src.suffix or ".webp"
    target = dest_dir / f"{filename}{ext}"
    shutil.copy2(src, target)
    return f"assets/owner/{target.name}"


def build_owner_overlay_css(
    order_id: str,
    design: dict[str, Any],
    *,
    logo_url: str | None = None,
    banner_urls: list[str] | None = None,
) -> str:
    colors = design.get("colors") or {}
    typo = design.get("typography") or {}
    home = design.get("homepage") or {}
    preset = _font_preset(str(typo.get("font_preset") or "dm_fraunces"))
    scale = float(typo.get("heading_scale") or 1.0)
    body_px = int(typo.get("body_size_px") or 16)
    banners = banner_urls or []
    primary_banner = banners[0] if banners else None

    hide_rules: list[str] = []
    section_map = {
        "hero": ".hero",
        "categories": "#categories, section#categories",
        "featured": "#featured, section#featured",
        "new_arrivals": "#new-arrivals, section#new-arrivals",
        "bestsellers": "#bestsellers, section#bestsellers",
        "reviews": "#reviews, section#reviews, .reviews",
        "newsletter": ".newsletter, section.newsletter, #newsletter",
        "footer": "footer, .site-footer",
    }
    for key, selector in section_map.items():
        if home.get(key) is False:
            hide_rules.append(f"{selector} {{ display: none !important; }}")

    logo_css = ""
    if logo_url:
        logo_css = f"""
.site-brand::before {{
  content: "";
  display: inline-block;
  width: 40px;
  height: 40px;
  margin-right: 0.6rem;
  background: url("{logo_url}") center/contain no-repeat;
  vertical-align: middle;
}}
"""

    hero_css = ""
    if primary_banner and home.get("hero", True) is not False:
        hero_css = f"""
.hero {{
  position: relative;
  background-image:
    linear-gradient(120deg, rgba(15,23,42,0.55), rgba(15,23,42,0.25)),
    url("{primary_banner}");
  background-size: cover;
  background-position: center;
  color: #fff;
  min-height: clamp(280px, 52vw, 520px);
}}
.hero .wrap {{ position: relative; z-index: 1; }}
.hero h1, .hero p, .hero-eyebrow {{ color: #fff; text-shadow: 0 2px 18px rgba(0,0,0,0.35); }}
@media (max-width: 720px) {{
  .hero {{
    min-height: clamp(240px, 70vw, 420px);
    background-position: center top;
  }}
}}
"""

    return f"""/* Owner Design Overlay — Virtus Store Admin R3.1.3 */
@import url("{preset['import']}");
:root {{
  --store-primary: {colors.get('primary') or '#0f766e'};
  --store-secondary: {colors.get('secondary') or '#f5f0e8'};
  --store-accent: {colors.get('link') or '#0d9488'};
  --store-bg: {colors.get('background') or '#faf7f2'};
  --store-button: {colors.get('button') or colors.get('primary') or '#0f766e'};
  --font-sans: {preset['sans']};
  --font-display: {preset['display']};
  --store-body-size: {body_px}px;
  --store-heading-scale: {scale};
}}
body {{
  font-family: var(--font-sans);
  font-size: var(--store-body-size);
  background-color: var(--store-bg);
}}
h1, h2, h3, .hero h1, .page-title {{
  font-family: var(--font-display);
}}
h1 {{ font-size: calc(2.4rem * var(--store-heading-scale)); }}
h2 {{ font-size: calc(1.6rem * var(--store-heading-scale)); }}
a {{ color: var(--store-accent); }}
.btn, button.btn, a.btn {{
  background: var(--store-button) !important;
}}
{logo_css}
{hero_css}
{chr(10).join(hide_rules)}
"""


def build_owner_overlay_js(
    design: dict[str, Any],
    *,
    favicon_url: str | None = None,
    banner_urls: list[str] | None = None,
) -> str:
    branding = design.get("branding") or {}
    name = str(branding.get("store_name") or "").replace("\\", "\\\\").replace("'", "\\'")
    tagline = str(branding.get("tagline") or "").replace("\\", "\\\\").replace("'", "\\'")
    banners = banner_urls or []
    banners_js = "[" + ",".join(f'"{b}"' for b in banners) + "]"
    fav_js = f'"{favicon_url}"' if favicon_url else "null"
    return f"""/* Owner Design Overlay JS */
(function(){{
  var name = '{name}';
  var tagline = '{tagline}';
  var fav = {fav_js};
  var banners = {banners_js};
  if (fav) {{
    var link = document.querySelector("link[rel*='icon']") || document.createElement('link');
    link.rel = 'icon';
    link.href = fav;
    document.head.appendChild(link);
  }}
  if (name) {{
    document.querySelectorAll('.site-brand, .brand-name, header .brand span').forEach(function(el){{
      if (el) el.textContent = name;
    }});
    var h1 = document.querySelector('.hero h1');
    if (h1) h1.textContent = name;
  }}
  if (tagline) {{
    var p = document.querySelector('.hero p');
    if (p) p.textContent = tagline;
  }}
  if (banners.length > 1) {{
    var hero = document.querySelector('.hero');
    if (!hero) return;
    var i = 0;
    setInterval(function(){{
      i = (i + 1) % banners.length;
      hero.style.backgroundImage = 'linear-gradient(120deg, rgba(15,23,42,0.55), rgba(15,23,42,0.25)), url(\"'+banners[i]+'\")';
    }}, 4500);
  }}
}})();
"""


def apply_design_to_product_dir(
    memory_dir: Path,
    order_id: str,
    product_dir: Path,
    *,
    store_name: str = "",
) -> bool:
    """
    Re-apply owner design into a freshly generated storefront.
    Copies owner media into assets/owner/ so the public live shop needs no auth.
    User Data Protection: never deletes store_admin design/products.
    """
    if not order_id or not product_dir.is_dir():
        return False
    svc = StoreDesignService(memory_dir)
    design_path = svc._order_dir(order_id) / "design.json"  # noqa: SLF001
    if not design_path.is_file():
        return False
    design = svc.raw_design(order_id, store_name=store_name)
    assets = product_dir / "assets"
    owner_dir = assets / "owner"
    if owner_dir.exists():
        shutil.rmtree(owner_dir)
    owner_dir.mkdir(parents=True, exist_ok=True)

    branding = design.get("branding") or {}
    logo_url = _copy_owner_asset(
        memory_dir, order_id, branding.get("logo"), owner_dir, "logo"
    )
    favicon_url = _copy_owner_asset(
        memory_dir, order_id, branding.get("favicon"), owner_dir, "favicon"
    )
    banner_urls: list[str] = []
    for i, b in enumerate((design.get("hero") or {}).get("banners") or []):
        if not isinstance(b, dict):
            continue
        url = _copy_owner_asset(
            memory_dir, order_id, b, owner_dir, f"banner_{i}"
        )
        if url:
            banner_urls.append(url)

    css = build_owner_overlay_css(
        order_id, design, logo_url=logo_url, banner_urls=banner_urls
    )
    js = build_owner_overlay_js(
        design, favicon_url=favicon_url, banner_urls=banner_urls
    )
    (assets / "owner-overlay.css").write_text(css, encoding="utf-8")
    (assets / "owner-overlay.js").write_text(js, encoding="utf-8")

    link = '<link rel="stylesheet" href="assets/owner-overlay.css" />'
    script = '<script src="assets/owner-overlay.js" defer></script>'
    for html_path in product_dir.glob("*.html"):
        html = html_path.read_text(encoding="utf-8")
        if "owner-overlay.css" not in html:
            if re.search(r"</head>", html, flags=re.I):
                html = re.sub(
                    r"</head>", f"  {link}\n</head>", html, count=1, flags=re.I
                )
            else:
                html = link + "\n" + html
        if "owner-overlay.js" not in html:
            if re.search(r"</body>", html, flags=re.I):
                html = re.sub(
                    r"</body>", f"  {script}\n</body>", html, count=1, flags=re.I
                )
            else:
                html = html + "\n" + script
        html_path.write_text(html, encoding="utf-8")
    return True
