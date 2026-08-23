"""Apply owner Website content + design overlay onto Factory HTML."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from app.integration.store_admin.design_service import FONT_PRESETS
from app.integration.website_admin.content_service import WebsiteContentService
from app.integration.website_admin.design_service import WebsiteDesignService


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
    if not isinstance(img, dict) or not img.get("path"):
        # try resolve via media id path stored on upload
        if not isinstance(img, dict) or not img.get("id"):
            return None
        svc = WebsiteContentService(memory_dir)
        found = svc.media.find_by_id(order_id, str(img["id"]))
        if found is None:
            return None
        src = found
    else:
        try:
            svc = WebsiteContentService(memory_dir)
            src = svc.media.resolve_path(str(img["path"]))
        except Exception:
            return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext = src.suffix or ".webp"
    target = dest_dir / f"{filename}{ext}"
    shutil.copy2(src, target)
    return f"assets/virtus-owner/{target.name}"


def build_owner_css(design: dict[str, Any], *, logo_url: str | None = None) -> str:
    colors = design.get("colors") or {}
    typo = design.get("typography") or {}
    motion = design.get("motion") or {}
    preset = _font_preset(str(typo.get("font_preset") or "dm_fraunces"))
    scale = float(typo.get("heading_scale") or 1.0)
    body_px = int(typo.get("body_size_px") or 16)
    anim = ""
    if motion.get("simple_animations") is not False:
        anim = """
@media (prefers-reduced-motion: no-preference) {
  .virtus-owner-fade { animation: virtusOwnerFade .6s ease both; }
  @keyframes virtusOwnerFade { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
}
"""
    logo_css = ""
    if logo_url:
        logo_css = f"""
.brand-logo-img, .site-logo img, header .logo img, .brand img {{
  content: url("{logo_url}");
  max-height: 48px;
  width: auto;
}}
"""
    return f"""/* Virtus Core Website Owner Overlay */
@import url("{preset["import"]}");
:root {{
  --virtus-primary: {colors.get("primary") or "#0f766e"};
  --virtus-secondary: {colors.get("secondary") or "#f5f0e8"};
  --virtus-button: {colors.get("button") or "#0f766e"};
  --virtus-link: {colors.get("link") or "#0d9488"};
  --virtus-bg: {colors.get("background") or "#faf7f2"};
  --virtus-text: {colors.get("text") or "#0f172a"};
  --virtus-font-sans: {preset["sans"]};
  --virtus-font-display: {preset["display"]};
  --virtus-body-size: {body_px}px;
  --virtus-heading-scale: {scale};
}}
body {{
  font-family: var(--virtus-font-sans) !important;
  font-size: var(--virtus-body-size) !important;
  color: var(--virtus-text);
  background-color: var(--virtus-bg);
}}
h1, h2, h3, .hero-title, .display, .brand-word {{
  font-family: var(--virtus-font-display) !important;
}}
h1 {{ font-size: calc(2.25rem * var(--virtus-heading-scale)) !important; }}
h2 {{ font-size: calc(1.75rem * var(--virtus-heading-scale)) !important; }}
a {{ color: var(--virtus-link); }}
.btn, .button, button.cta, a.cta, .hero-cta, .lx-cta {{
  background: var(--virtus-button) !important;
  border-color: var(--virtus-button) !important;
  color: #fff !important;
}}
{logo_css}
{anim}
"""


def build_owner_js(
    content: dict[str, Any],
    *,
    hero_image_url: str | None = None,
) -> str:
    payload = {
        "hero": content.get("hero") or {},
        "about": content.get("about") or {},
        "services": content.get("services") or [],
        "prices": content.get("prices") or {},
        "gallery": content.get("gallery") or [],
        "team": content.get("team") or [],
        "reviews": content.get("reviews") or [],
        "contacts": content.get("contacts") or {},
        "hours": content.get("hours") or {},
        "social": content.get("social") or {},
        "faq": content.get("faq") or [],
        "seo": content.get("seo") or {},
        "hero_image_url": hero_image_url,
    }
    data = json.dumps(payload, ensure_ascii=False)
    return f"""/* Virtus Core Website Owner Content */
(function(){{
  var C = {data};
  function setText(sel, text) {{
    if (!text) return;
    document.querySelectorAll(sel).forEach(function(el){{ el.textContent = text; }});
  }}
  function ensureSection(id, title) {{
    var existing = document.getElementById(id);
    if (existing) return existing;
    var sec = document.createElement('section');
    sec.id = id;
    sec.className = 'virtus-owner-section virtus-owner-fade';
    sec.style.cssText = 'max-width:1100px;margin:48px auto;padding:0 20px';';
    var h = document.createElement('h2');
    h.textContent = title || '';
    sec.appendChild(h);
    var body = document.body;
    if (body) body.appendChild(sec);
    return sec;
  }}
  try {{
    var h = C.hero || {{}};
    setText('h1, .hero-title, .lx-hero-title, [data-virtus=\"hero-headline\"]', h.headline);
    setText('.hero p, .hero-sub, .lx-hero-sub, [data-virtus=\"hero-sub\"]', h.subheadline);
    setText('.hero .cta, .hero-cta, a.cta, [data-virtus=\"hero-cta\"]', h.cta_label);
    if (C.hero_image_url) {{
      var heroMedia = document.querySelector('.hero-photo, .lx-hero-media img, .ed-hero-media img, [data-virtus=\"hero-image\"]');
      if (heroMedia && heroMedia.tagName === 'IMG') heroMedia.src = C.hero_image_url;
      var heroBg = document.querySelector('.hero, .lx-hero, [data-virtus=\"hero\"]');
      if (heroBg) {{
        heroBg.style.backgroundImage = 'linear-gradient(120deg,rgba(15,23,42,.45),rgba(15,23,42,.2)), url(\"'+C.hero_image_url+'\")';
        heroBg.style.backgroundSize = 'cover';
        heroBg.style.backgroundPosition = 'center';
      }}
    }}
    var about = C.about || {{}};
    if (about.title || about.body) {{
      setText('[data-virtus=\"about-title\"], #about h2, .about h2', about.title);
      setText('[data-virtus=\"about-body\"], #about p, .about p', about.body);
    }}
    if (C.services && C.services.length) {{
      var svcRoot = document.querySelector('[data-virtus=\"services\"], .services, #services');
      if (svcRoot) {{
        var cards = svcRoot.querySelectorAll('.service-card, .svc-card, article, li');
        C.services.forEach(function(svc, i) {{
          var card = cards[i];
          if (!card) return;
          var t = card.querySelector('h3, h4, .title, [data-virtus=\"service-title\"]');
          var d = card.querySelector('p, .desc, [data-virtus=\"service-desc\"]');
          if (t && svc.title) t.textContent = svc.title;
          if (d && svc.description) d.textContent = svc.description;
        }});
      }}
    }}
    if (C.prices && C.prices.enabled) {{
      var priceSec = ensureSection('virtus-owner-prices', C.prices.title || 'Preise');
      var intro = priceSec.querySelector('.virtus-prices-intro');
      if (!intro) {{
        intro = document.createElement('p');
        intro.className = 'virtus-prices-intro';
        priceSec.appendChild(intro);
      }}
      intro.textContent = C.prices.intro || '';
      var list = priceSec.querySelector('.virtus-prices-list');
      if (!list) {{
        list = document.createElement('div');
        list.className = 'virtus-prices-list';
        list.style.cssText = 'display:grid;gap:12px;margin-top:16px';';
        priceSec.appendChild(list);
      }}
      list.innerHTML = '';
      (C.prices.items || []).forEach(function(item) {{
        var row = document.createElement('div');
        row.style.cssText = 'display:flex;justify-content:space-between;gap:12px;padding:12px 0;border-bottom:1px solid rgba(0,0,0,.08)';
        row.innerHTML = '<strong>'+ (item.label||'') +'</strong><span>'+ (item.price||'') +'</span>';
        list.appendChild(row);
      }});
    }}
    if (C.reviews && C.reviews.length) {{
      setText('[data-virtus=\"review-text\"]', (C.reviews[0] && C.reviews[0].text) || '');
      setText('[data-virtus=\"review-author\"]', (C.reviews[0] && C.reviews[0].author) || '');
    }}
    var phone = (C.contacts && C.contacts.phone) || '';
    var email = (C.contacts && C.contacts.email) || '';
    var address = (C.contacts && C.contacts.address) || '';
    if (phone) {{
      document.querySelectorAll('a[href^=\"tel:\"]').forEach(function(a){{ a.href='tel:'+phone.replace(/\\s+/g,''); a.textContent = phone; }});
      setText('[data-virtus=\"phone\"]', phone);
    }}
    if (email) {{
      document.querySelectorAll('a[href^=\"mailto:\"]').forEach(function(a){{ a.href='mailto:'+email; a.textContent = email; }});
      setText('[data-virtus=\"email\"]', email);
    }}
    if (address) setText('[data-virtus=\"address\"], .address, .contact-address', address);
    if (C.seo && C.seo.title) document.title = C.seo.title;
    var md = document.querySelector('meta[name=\"description\"]');
    if (md && C.seo && C.seo.description) md.setAttribute('content', C.seo.description);
    document.documentElement.setAttribute('data-virtus-owner', '1');
  }} catch (e) {{}}
}})();
"""

def apply_website_overlay_to_product_dir(
    memory_dir: Path,
    order_id: str,
    product_dir: Path,
    *,
    business_name: str = "",
    seed_meta: dict[str, Any] | None = None,
) -> bool:
    """
    Re-apply owner content+design into generated website HTML.
    User Data Protection: never deletes website_admin overlays.
    """
    if not order_id or not product_dir.is_dir():
        return False

    content_svc = WebsiteContentService(memory_dir)
    design_svc = WebsiteDesignService(memory_dir)
    content = content_svc.raw_content(order_id, seed_meta=seed_meta)
    design = design_svc.raw_design(order_id, business_name=business_name)

    assets = product_dir / "assets"
    owner_dir = assets / "virtus-owner"
    if owner_dir.exists():
        shutil.rmtree(owner_dir)
    owner_dir.mkdir(parents=True, exist_ok=True)

    branding = design.get("branding") or {}
    logo_url = _copy_owner_asset(
        memory_dir, order_id, branding.get("logo"), owner_dir, "logo"
    )
    hero_img = (content.get("hero") or {}).get("image")
    hero_url = _copy_owner_asset(
        memory_dir, order_id, hero_img, owner_dir, "hero"
    )

    css = build_owner_css(design, logo_url=logo_url)
    js = build_owner_js(content, hero_image_url=hero_url)
    (assets / "virtus-owner.css").write_text(css, encoding="utf-8")
    (assets / "virtus-owner.js").write_text(js, encoding="utf-8")
    (assets / "virtus-owner-content.json").write_text(
        json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    link = '<link rel="stylesheet" href="assets/virtus-owner.css" data-virtus-owner="1" />'
    script = '<script src="assets/virtus-owner.js" defer data-virtus-owner="1"></script>'
    for html_path in product_dir.glob("*.html"):
        html = html_path.read_text(encoding="utf-8")
        if "virtus-owner.css" not in html:
            if re.search(r"</head>", html, flags=re.I):
                html = re.sub(
                    r"</head>", f"  {link}\n</head>", html, count=1, flags=re.I
                )
            else:
                html = link + "\n" + html
        if "virtus-owner.js" not in html:
            if re.search(r"</body>", html, flags=re.I):
                html = re.sub(
                    r"</body>", f"  {script}\n</body>", html, count=1, flags=re.I
                )
            else:
                html = html + "\n" + script
        html_path.write_text(html, encoding="utf-8")
    return True
