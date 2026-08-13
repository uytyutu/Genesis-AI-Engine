# -*- coding: utf-8 -*-
"""Compose Premium Website + Shop HTML from CreativeBusinessProject SSOT.

Universal — not LORENNE-only. LORENNE is the first proof input.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from app.factory.cinema_scroll import cinema_scroll_script


def _esc(s: Any) -> str:
    return (
        str(s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def brand_slug(name: str) -> str:
    out = []
    for ch in (name or "brand").lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in " -_":
            out.append("-")
    s = "".join(out).strip("-")
    while "--" in s:
        s = s.replace("--", "-")
    return s[:48] or "brand"


def _products_from_cbp(project: dict[str, Any]) -> list[dict[str, Any]]:
    biz = project.get("business") or {}
    cats = list((project.get("shop_catalog_plan") or {}).get("categories") or []) or [
        "Premium",
        "Special Moments",
        "Self Care",
    ]
    names = list(biz.get("products") or biz.get("products_or_services") or [])
    if not names:
        names = ["Signature Set", "Classic Set", "Premium Set"]
    # Expand to catalog depth planned in SSOT (demo-labeled)
    want = int((project.get("shop_catalog_plan") or {}).get("min_demo_products") or len(names))
    want = max(len(names), min(40, want))
    items: list[dict[str, Any]] = []
    base_prices = [39, 42, 45, 48, 49, 51, 52, 54, 55, 58, 59, 69, 79]
    for i in range(want):
        name = names[i % len(names)]
        if i >= len(names):
            name = f"{name} · Edition {i - len(names) + 1}"
        items.append(
            {
                "id": f"p{i+1}",
                "name": name,
                "cat": cats[i % len(cats)],
                "price": float(base_prices[i % len(base_prices)]),
                "frame": (i % max(1, int((project.get("cinematic") or {}).get("state_count") or 12))) + 1,
            }
        )
    return items


def _copy_lines(project: dict[str, Any]) -> list[str]:
    m = project.get("marketing") or {}
    lines = list(m.get("scroll_lines") or m.get("marketing_lines") or [])
    if not lines:
        board = project.get("storyboard") or {}
        lines = list(board.get("marketing_lines") or [])
    if not lines:
        brand = (project.get("brand") or {}).get("name") or "Brand"
        lines = [f"{brand}.", str(m.get("headline_hint") or "Premium."), str(m.get("cta") or "Jetzt entdecken")]
    return lines


def attach_sequence_assets(
    *,
    dest_seq: Path,
    source_seq: Path | None,
    frame_count: int,
) -> dict[str, Any]:
    """Attach existing coherent frames if provided; else leave slots for generation."""
    dest_seq.mkdir(parents=True, exist_ok=True)
    attached = 0
    missing: list[int] = []
    for i in range(1, frame_count + 1):
        dest = dest_seq / f"f{i:03d}.jpg"
        src = None
        if source_seq and source_seq.is_dir():
            for cand in (source_seq / f"f{i:03d}.jpg", source_seq / f"f{i:03d}.png", source_seq / f"f{i:02d}.jpg"):
                if cand.is_file():
                    src = cand
                    break
            # fallback: reuse last available source frame for bridges
            if src is None:
                files = sorted(source_seq.glob("f*.jpg")) + sorted(source_seq.glob("f*.png"))
                if files:
                    src = files[min(i - 1, len(files) - 1)]
        if src and src.is_file():
            shutil.copy2(src, dest)
            attached += 1
        else:
            missing.append(i)
    return {
        "attached": attached,
        "missing": missing,
        "source": str(source_seq) if source_seq else None,
        "complete": attached >= frame_count and not missing,
    }


def compose_premium_website(
    project: dict[str, Any],
    *,
    out_dir: Path,
    shop_rel: str = "../shop/index.html",
) -> dict[str, Any]:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    biz = project.get("business") or {}
    brand = str((project.get("brand") or {}).get("name") or biz.get("business_name") or "Brand")
    city = str(biz.get("city") or "")
    cta = str((project.get("cta_strategy") or {}).get("primary") or (project.get("marketing") or {}).get("cta") or "Jetzt entdecken")
    lines = _copy_lines(project)
    beats = list((project.get("storyboard") or {}).get("beats") or [])
    n = max(1, len(beats))
    copies = [lines[i % len(lines)] for i in range(n)]
    imgs = "".join(
        f'<img src="assets/seq/f{i:03d}.jpg" alt="" class="{"is-on" if i == 1 else ""}" data-i="{i}" />'
        for i in range(1, n + 1)
    )
    about = str((project.get("marketing") or {}).get("about_hint") or biz.get("description") or "")[:480]
    reviews = """
      <article class="review"><p class="stars">★★★★★</p><p>Genau das Gefühl, das wir wollten.</p><span class="demo-tag">DEMO REVIEW</span></article>
      <article class="review"><p class="stars">★★★★★</p><p>Elegant, persönlich, hochwertig.</p><span class="demo-tag">DEMO REVIEW</span></article>
      <article class="review"><p class="stars">★★★★☆</p><p>Schöne Zusammenstellung — klarer Auftritt.</p><span class="demo-tag">DEMO REVIEW</span></article>
    """
    contacts = project.get("contacts") or {}
    email_note = (
        f"E-Mail: {_esc(contacts.get('email'))}"
        if str(contacts.get("email") or "").strip()
        else "E-Mail und Telefon erscheinen hier, sobald Sie sie im Workspace hinterlegen — keine erfundenen Konten."
    )
    year = "2026"
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_esc(brand)} · Premium</title>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600&family=Outfit:wght@300;400;600&display=swap" rel="stylesheet" />
  <style>
    :root {{ --bg:#0a0710; --ink:#f6f0f8; --muted:#c9bfd4; --accent:#c4a0e0; --line:rgba(255,255,255,.12); }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Outfit,system-ui,sans-serif; }}
    a {{ color:inherit; text-decoration:none; }}
    header.nav {{ position:fixed; inset:0 0 auto 0; z-index:30; display:flex; justify-content:space-between; align-items:center;
      padding:.85rem 1.2rem; background:rgba(10,7,16,.72); backdrop-filter:blur(10px); border-bottom:1px solid var(--line); }}
    header.nav strong {{ font-family:"Cormorant Garamond",serif; font-size:1.35rem; letter-spacing:.04em; }}
    header.nav nav {{ display:flex; gap:.9rem; flex-wrap:wrap; align-items:center; font-size:.9rem; }}
    .nav-cta {{ border-radius:999px; padding:.55rem 1rem; background:linear-gradient(135deg,var(--accent),#e8d5f5); color:#1a1020; font-weight:600; }}
    #cinemaPin {{ height:{max(180, n * 42)}vh; position:relative; }}
    .cinema-sticky {{ position:sticky; top:0; height:100vh; overflow:hidden; }}
    #seq {{ position:absolute; inset:0; }}
    #seq img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; opacity:0; transition:opacity .06s linear; }}
    #seq img.is-on {{ opacity:1; }}
    #seq img.is-prev {{ opacity:.35; }}
    .cinema-ui {{ position:absolute; inset:auto 0 0 0; padding:1.4rem 1.2rem 2rem; background:linear-gradient(to top,rgba(10,7,16,.92),transparent); }}
    .cinema-ui p {{ margin:0; font-family:"Cormorant Garamond",serif; font-size:clamp(1.6rem,4vw,2.6rem); }}
    .meter {{ margin-top:.5rem; font-size:.7rem; letter-spacing:.14em; color:var(--muted); }}
    .prog {{ margin-top:.6rem; height:2px; background:rgba(255,255,255,.15); }}
    .prog > i {{ display:block; height:100%; width:100%; transform:scaleX(0); transform-origin:left center; background:var(--accent); will-change:transform; }}
    .section {{ max-width:70rem; margin:0 auto; padding:3.5rem 1.2rem; }}
    .section h2 {{ font-family:"Cormorant Garamond",serif; font-size:clamp(1.8rem,3vw,2.4rem); margin:0 0 .8rem; }}
    .lead {{ color:var(--muted); line-height:1.65; max-width:40rem; }}
    .cta {{ display:inline-block; margin-top:1rem; border-radius:999px; padding:.7rem 1.2rem; background:linear-gradient(135deg,var(--accent),#e8d5f5); color:#1a1020; font-weight:600; }}
    .grid-cards {{ display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); margin-top:1.2rem; }}
    .review {{ border:1px solid var(--line); border-radius:1rem; padding:1rem; background:rgba(255,255,255,.03); }}
    .demo-tag {{ display:inline-block; margin-top:.6rem; font-size:.65rem; letter-spacing:.1em; color:var(--accent); }}
    .stars {{ color:#e8d5f5; margin:0 0 .4rem; }}
    .contact-shell {{ display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); }}
    .contact-panel {{ border:1px solid var(--line); border-radius:1rem; padding:1.1rem; }}
    label {{ display:block; margin:.5rem 0; font-size:.82rem; color:var(--muted); }}
    input, textarea {{ width:100%; margin-top:.25rem; border-radius:.65rem; border:1px solid var(--line); background:#120c18; color:var(--ink); padding:.55rem .7rem; font:inherit; }}
    footer.site {{ border-top:1px solid var(--line); padding:1.4rem 1.2rem 2.4rem; color:var(--muted); font-size:.8rem; text-align:center; }}
    footer.site a {{ color:var(--accent); }}
  </style>
</head>
<body>
  <header class="nav">
    <strong>{_esc(brand)}</strong>
    <nav>
      <a href="#about">Über uns</a>
      <a href="{_esc(shop_rel)}">Shop</a>
      <a href="#kontakt">Kontakt</a>
      <a href="impressum.html">Impressum</a>
      <a class="nav-cta" href="#kontakt">{_esc(cta)}</a>
    </nav>
  </header>

  <div id="cinemaPin">
    <div class="cinema-sticky">
      <div id="seq">{imgs}</div>
      <div class="cinema-ui">
        <p id="beatLine">{_esc(copies[0] if copies else brand)}</p>
        <div class="meter" id="meter">FRAME 001 / {n:03d}</div>
        <div class="prog"><i id="prog"></i></div>
      </div>
    </div>
  </div>

  <section class="section" id="about">
    <h2>{_esc(brand)}{_esc(f" · {city}" if city else "")}</h2>
    <p class="lead">{_esc(about)}</p>
    <a class="cta" href="{_esc(shop_rel)}">Zum Online-Shop →</a>
  </section>

  <section class="section" id="reviews">
    <h2>Kundenbewertungen</h2>
    <div class="grid-cards">{reviews}</div>
  </section>

  <section class="section" id="kontakt">
    <h2>Kontakt</h2>
    <div class="contact-shell">
      <div class="contact-panel">
        <p class="lead">{_esc(city or "Deutschland")} · {_esc(brand)}</p>
        <p class="lead" style="margin-top:.6rem">{email_note}</p>
      </div>
      <div class="contact-panel">
        <form class="msg" onsubmit="event.preventDefault(); this.querySelector('.ok').style.display='block';">
          <label>Name<input name="name" required autocomplete="name" /></label>
          <label>Email<input type="email" name="email" required autocomplete="email" /></label>
          <label>Nachricht<textarea name="msg" rows="4" required></textarea></label>
          <button class="cta" type="submit">Nachricht senden</button>
          <p class="ok" style="display:none;color:#b8f0c8">Danke — Nachricht (Demo) erfasst.</p>
        </form>
      </div>
    </div>
  </section>

  <footer class="site">
    {_esc(brand)}{_esc(f" · {city}" if city else "")} · seit {year}<br />
    <a href="impressum.html">Impressum</a> ·
    <a href="datenschutz.html">Datenschutz</a> ·
    <a href="#about">Über uns</a> ·
    <a href="{_esc(shop_rel)}">Online-Shop</a>
  </footer>

  <script>
  {cinema_scroll_script(copies_js=json.dumps(copies, ensure_ascii=False))}
  </script>
</body>
</html>
"""
    (dest / "index.html").write_text(html, encoding="utf-8")
    _write_legal(dest, brand, city, contacts)
    (dest / "project_snapshot.json").write_text(
        json.dumps(
            {
                "project_id": project.get("project_id"),
                "brand": brand,
                "frames": n,
                "engine": "cbp_premium_composer_v1",
                "quality_state": project.get("quality_state"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {"ok": True, "path": str(dest), "frames": n, "kind": "website"}


def compose_premium_shop(
    project: dict[str, Any],
    *,
    out_dir: Path,
    website_rel: str = "../website/index.html",
    seq_rel_for_hero: str = "../website/assets/seq/f010.jpg",
) -> dict[str, Any]:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    assets = dest / "assets" / "products"
    assets.mkdir(parents=True, exist_ok=True)
    biz = project.get("business") or {}
    brand = str((project.get("brand") or {}).get("name") or biz.get("business_name") or "Brand")
    products = _products_from_cbp(project)
    cats = sorted({p["cat"] for p in products})
    cat_nav = "".join(f'<button type="button" class="chip" data-cat="{_esc(c)}">{_esc(c)}</button>' for c in ["Alle", *cats])

    # Map product images from website seq if present
    web_seq = dest.parent / "website" / "assets" / "seq"
    if not web_seq.is_dir():
        web_seq = Path(out_dir).parent / "website" / "assets" / "seq"
    products_html = []
    for i, p in enumerate(products):
        src = web_seq / f"f{int(p['frame']):03d}.jpg"
        local = assets / f"p{i+1:02d}.jpg"
        if src.is_file():
            shutil.copy2(src, local)
        rel = f"assets/products/{local.name}"
        products_html.append(
            f'<article class="product" id="p{i+1}">'
            f'<a href="#p{i+1}"><img src="{_esc(rel)}" alt="" /></a>'
            f'<p class="cat">{_esc(p["cat"])}</p>'
            f'<h3>{_esc(p["name"])}</h3>'
            f'<p class="price">{p["price"]:.0f} €</p>'
            f'<button type="button" class="cta add" data-name="{_esc(p["name"])}" data-price="{p["price"]}">In den Warenkorb</button>'
            f"</article>"
        )

    cart_key = f"{brand_slug(brand)}_shop_cart_v1"
    orders_key = f"{brand_slug(brand)}_shop_orders_v1"
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_esc(brand)} Shop</title>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600&family=Outfit:wght@300;400;600&display=swap" rel="stylesheet" />
  <style>
    :root {{ --bg:#0a0710; --ink:#f6f0f8; --muted:#c9bfd4; --accent:#c4a0e0; --line:rgba(255,255,255,.12); }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Outfit,system-ui,sans-serif; }}
    a {{ color:inherit; text-decoration:none; }}
    header {{ position:sticky; top:0; z-index:20; display:flex; justify-content:space-between; align-items:center; gap:1rem; flex-wrap:wrap;
      padding:.85rem 1.1rem; background:rgba(10,7,16,.92); border-bottom:1px solid var(--line); backdrop-filter:blur(8px); }}
    header strong {{ font-family:"Cormorant Garamond",serif; font-size:1.25rem; }}
    .cta {{ border:0; border-radius:999px; padding:.65rem 1.1rem; background:linear-gradient(135deg,var(--accent),#e8d5f5); color:#1a1020; font-weight:600; cursor:pointer; font:inherit; min-height:44px; }}
    .cta.ghost {{ background:transparent; color:var(--ink); border:1px solid var(--line); }}
    .hero {{ position:relative; min-height:70vh; display:grid; place-items:end start; padding:2rem 1.25rem 3rem;
      background:url('{_esc(seq_rel_for_hero)}') center/cover; }}
    .hero::after {{ content:""; position:absolute; inset:0; background:linear-gradient(to top,rgba(10,7,16,.92),rgba(10,7,16,.25)); }}
    .hero-inner {{ position:relative; z-index:1; max-width:40rem; }}
    .hero h1 {{ font-family:"Cormorant Garamond",serif; font-size:clamp(2.4rem,6vw,4rem); margin:0 0 .5rem; }}
    .hero p {{ color:var(--muted); font-size:1.1rem; line-height:1.6; }}
    .wrap {{ max-width:72rem; margin:0 auto; padding:2rem 1.25rem 4rem; }}
    .chips {{ display:flex; flex-wrap:wrap; gap:.5rem; margin:1rem 0 1.5rem; }}
    .chip {{ border:1px solid var(--line); background:transparent; color:var(--muted); border-radius:999px; padding:.45rem .85rem; cursor:pointer; font:inherit; }}
    .chip.on {{ color:#1a1020; background:var(--accent); border-color:transparent; }}
    .grid {{ display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); }}
    .product {{ border:1px solid var(--line); border-radius:1rem; overflow:hidden; background:rgba(255,255,255,.03); display:flex; flex-direction:column; }}
    .product img {{ width:100%; aspect-ratio:1; object-fit:cover; background:#1a1020; }}
    .product .cat {{ margin:.7rem .85rem 0; font-size:.7rem; letter-spacing:.12em; text-transform:uppercase; color:var(--accent); }}
    .product h3 {{ margin:.35rem .85rem; font-size:1rem; }}
    .product .price {{ margin:0 .85rem .5rem; color:var(--accent); font-weight:600; }}
    .product .add {{ margin:.2rem .85rem 1rem; }}
    .muted {{ color:var(--muted); font-size:.85rem; }}
    .drawer-bg {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,.55); z-index:40; }}
    .drawer-bg.on {{ display:block; }}
    .drawer {{ position:fixed; top:0; right:0; z-index:50; width:min(26rem,100%); height:100%; overflow:auto;
      background:#120c18; border-left:1px solid var(--line); padding:1.1rem; transform:translateX(110%); transition:transform .25s ease; }}
    .drawer.on {{ transform:none; }}
    .cart-line {{ display:flex; justify-content:space-between; gap:.5rem; padding:.45rem 0; border-bottom:1px solid var(--line); font-size:.9rem; }}
    label {{ display:block; margin:.55rem 0; font-size:.82rem; color:var(--muted); }}
    input, select, textarea {{ width:100%; margin-top:.25rem; border-radius:.65rem; border:1px solid var(--line); background:#0a0710; color:var(--ink); padding:.55rem .7rem; font:inherit; }}
    .warn {{ margin:.8rem 0; padding:.7rem .8rem; border-radius:.75rem; border:1px solid rgba(232,180,255,.35); background:rgba(196,160,224,.08); font-size:.82rem; line-height:1.45; }}
    .ok {{ color:#b8f0c8; }}
    footer {{ border-top:1px solid var(--line); padding:1.5rem; text-align:center; color:var(--muted); font-size:.8rem; }}
    footer a {{ color:var(--accent); }}
  </style>
</head>
<body>
  <header>
    <strong>{_esc(brand)} Shop</strong>
    <nav style="display:flex;gap:.75rem;align-items:center;flex-wrap:wrap">
      <a href="{_esc(website_rel)}">Website</a>
      <a href="#catalog">Katalog</a>
      <a href="impressum.html">Impressum</a>
      <button type="button" class="cta" id="cartBtn">Warenkorb (<span id="cartCount">0</span>)</button>
    </nav>
  </header>
  <section class="hero">
    <div class="hero-inner">
      <p class="muted" style="letter-spacing:.2em;text-transform:uppercase;font-size:.7rem;color:var(--accent)">Desire → Product → Purchase</p>
      <h1>{_esc((project.get("marketing") or {}).get("headline_hint") or brand)}</h1>
      <p>{_esc((project.get("marketing") or {}).get("shop_lead") or "Premium Online-Shop — dieselbe visuelle Welt wie die Website.")}</p>
      <p style="margin-top:1rem"><a class="cta" href="#catalog">Katalog öffnen</a></p>
    </div>
  </section>
  <main class="wrap" id="catalog">
    <h2 style="font-family:'Cormorant Garamond',serif;font-size:2rem;margin:0">Katalog · {len(products)} Artikel</h2>
    <div class="chips" id="chips">{cat_nav}</div>
    <div class="grid" id="grid">{''.join(products_html)}</div>
  </main>
  <div class="drawer-bg" id="drawerBg"></div>
  <aside class="drawer" id="cartDrawer">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:1rem">
      <h2 id="drawerTitle">Warenkorb</h2>
      <button type="button" class="cta ghost" id="closeDrawer">Schließen</button>
    </div>
    <div id="cartStep">
      <div id="cartList"></div>
      <p style="margin:1rem 0">Zwischensumme: <strong id="cartSum">0</strong> €</p>
      <button type="button" class="cta" id="toCheckout" style="width:100%">Zur Kasse</button>
    </div>
    <form id="checkoutStep" style="display:none" novalidate>
      <p class="muted">Lieferadresse · Versand · Zahlung</p>
      <label>Vor- und Nachname<input name="name" required autocomplete="name" /></label>
      <label>E-Mail<input type="email" name="email" required autocomplete="email" /></label>
      <label>Telefon<input type="tel" name="phone" autocomplete="tel" /></label>
      <label>Straße und Hausnummer<input name="street" required autocomplete="street-address" /></label>
      <label>PLZ<input name="zip" required autocomplete="postal-code" pattern="[0-9]{{5}}" /></label>
      <label>Ort<input name="city" required autocomplete="address-level2" /></label>
      <label>Land<select name="country"><option value="DE" selected>Deutschland</option><option value="AT">Österreich</option><option value="CH">Schweiz</option></select></label>
      <label>Versandart
        <select name="shipping" id="shipping">
          <option value="dhl_std" data-fee="4.90">DHL Standard — 4,90 €</option>
          <option value="dhl_exp" data-fee="9.90">DHL Express — 9,90 €</option>
          <option value="pickup" data-fee="0">Abholung — 0 €</option>
        </select>
      </label>
      <p class="muted">Versand: <strong id="shipFee">4,90</strong> € · Gesamt: <strong id="grandTotal">0</strong> €</p>
      <p class="warn">Zahlung über den Shop der Händlerin (Stripe Connect). Status: <strong>Nicht verbunden</strong>. Bestellung wird als Anfrage gespeichert.</p>
      <label>Hinweis (optional)<textarea name="note" rows="2"></textarea></label>
      <button type="submit" class="cta" style="width:100%;margin-top:.8rem">Bestellung absenden</button>
      <button type="button" class="cta ghost" id="backCart" style="width:100%;margin-top:.5rem">Zurück zum Warenkorb</button>
    </form>
    <div id="doneStep" style="display:none">
      <p class="ok">Vielen Dank — Bestellung <strong id="orderId"></strong> erfasst.</p>
      <button type="button" class="cta" id="doneClose" style="width:100%;margin-top:1rem">Weiter einkaufen</button>
    </div>
  </aside>
  <footer>
    {_esc(brand)} · seit 2026<br />
    <a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a> · <a href="agb.html">AGB</a> ·
    <a href="{_esc(website_rel)}">Website</a>
  </footer>
  <script>
  (function(){{
    var KEY = {json.dumps(cart_key)};
    var ORDERS = {json.dumps(orders_key)};
    var cart = [];
    try {{ cart = JSON.parse(localStorage.getItem(KEY) || '[]') || []; }} catch (e) {{ cart = []; }}
    var chips = document.querySelectorAll('.chip');
    var products = document.querySelectorAll('.product');
    var drawer = document.getElementById('cartDrawer');
    var bg = document.getElementById('drawerBg');
    function save(){{ try {{ localStorage.setItem(KEY, JSON.stringify(cart)); }} catch(e){{}} }}
    function money(n){{ return (Math.round(n * 100) / 100).toFixed(2).replace('.', ','); }}
    function subtotal(){{ return cart.reduce(function(a,b){{ return a + Number(b.price||0); }}, 0); }}
    function shipFee(){{
      var sel = document.getElementById('shipping');
      var opt = sel.options[sel.selectedIndex];
      return parseFloat(opt.getAttribute('data-fee') || '0');
    }}
    function openDrawer(){{ drawer.classList.add('on'); bg.classList.add('on'); }}
    function closeDrawer(){{ drawer.classList.remove('on'); bg.classList.remove('on'); }}
    function renderCart(){{
      document.getElementById('cartCount').textContent = String(cart.length);
      var list = document.getElementById('cartList');
      if (!cart.length) list.innerHTML = '<p class="muted">Ihr Warenkorb ist leer.</p>';
      else list.innerHTML = cart.map(function(x,i){{
        return '<div class="cart-line"><span>'+x.name+'</span><span>'+money(x.price)+' € <button type="button" data-i="'+i+'" class="rm" style="margin-left:.4rem;border:0;background:transparent;color:#e8b4ff;cursor:pointer">✕</button></span></div>';
      }}).join('');
      document.getElementById('cartSum').textContent = money(subtotal());
      document.getElementById('grandTotal').textContent = money(subtotal() + shipFee());
      document.getElementById('shipFee').textContent = money(shipFee());
      list.querySelectorAll('.rm').forEach(function(btn){{
        btn.addEventListener('click', function(){{
          cart.splice(parseInt(btn.getAttribute('data-i'),10), 1); save(); renderCart();
        }});
      }});
    }}
    chips.forEach(function(ch){{
      ch.addEventListener('click', function(){{
        chips.forEach(function(c){{ c.classList.remove('on'); }});
        ch.classList.add('on');
        var cat = ch.getAttribute('data-cat');
        products.forEach(function(p){{
          p.style.display = (cat === 'Alle' || p.querySelector('.cat').textContent === cat) ? '' : 'none';
        }});
      }});
    }});
    if (chips[0]) chips[0].classList.add('on');
    document.querySelectorAll('.add').forEach(function(btn){{
      btn.addEventListener('click', function(){{
        cart.push({{ name: btn.getAttribute('data-name'), price: parseFloat(btn.getAttribute('data-price')) }});
        save(); renderCart();
        document.getElementById('cartStep').style.display = '';
        document.getElementById('checkoutStep').style.display = 'none';
        document.getElementById('doneStep').style.display = 'none';
        openDrawer();
      }});
    }});
    document.getElementById('cartBtn').addEventListener('click', function(){{ renderCart(); openDrawer(); }});
    document.getElementById('closeDrawer').addEventListener('click', closeDrawer);
    document.getElementById('drawerBg').addEventListener('click', closeDrawer);
    document.getElementById('shipping').addEventListener('change', renderCart);
    document.getElementById('toCheckout').addEventListener('click', function(){{
      if (!cart.length) return;
      document.getElementById('cartStep').style.display = 'none';
      document.getElementById('checkoutStep').style.display = '';
      document.getElementById('drawerTitle').textContent = 'Kasse';
      renderCart();
    }});
    document.getElementById('backCart').addEventListener('click', function(){{
      document.getElementById('checkoutStep').style.display = 'none';
      document.getElementById('cartStep').style.display = '';
      document.getElementById('drawerTitle').textContent = 'Warenkorb';
    }});
    document.getElementById('checkoutStep').addEventListener('submit', function(ev){{
      ev.preventDefault();
      if (!cart.length) return;
      var fd = new FormData(ev.target);
      var order = {{
        id: 'ORD-' + Date.now().toString(36).toUpperCase(),
        items: cart.slice(), subtotal: subtotal(), shipping_fee: shipFee(),
        total: subtotal() + shipFee(), shipping: fd.get('shipping'),
        customer: {{ name: fd.get('name'), email: fd.get('email'), phone: fd.get('phone'),
          street: fd.get('street'), zip: fd.get('zip'), city: fd.get('city'), country: fd.get('country'), note: fd.get('note') }},
        payment_status: 'awaiting_merchant_connect'
      }};
      try {{
        var hist = JSON.parse(localStorage.getItem(ORDERS) || '[]');
        hist.unshift(order);
        localStorage.setItem(ORDERS, JSON.stringify(hist.slice(0, 40)));
      }} catch (e) {{}}
      cart = []; save(); renderCart();
      document.getElementById('checkoutStep').style.display = 'none';
      document.getElementById('doneStep').style.display = '';
      document.getElementById('orderId').textContent = order.id;
      ev.target.reset();
    }});
    document.getElementById('doneClose').addEventListener('click', closeDrawer);
    renderCart();
  }})();
  </script>
</body>
</html>
"""
    (dest / "index.html").write_text(html, encoding="utf-8")
    _write_legal(dest, brand, str(biz.get("city") or ""), project.get("contacts") or {}, agb=True)
    (dest / "catalog.json").write_text(
        json.dumps({"products": products, "demo": True, "brand": brand}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"ok": True, "path": str(dest), "products": len(products), "kind": "shop"}


def _write_legal(
    dest: Path,
    brand: str,
    city: str,
    contacts: dict[str, Any],
    *,
    agb: bool = False,
) -> None:
    email = str(contacts.get("email") or "").strip() or "im Workspace hinterlegen"
    (dest / "impressum.html").write_text(
        f"<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'/><title>Impressum · {_esc(brand)}</title></head>"
        f"<body style='font-family:system-ui;background:#0a0710;color:#f6f0f8;padding:2rem'>"
        f"<p><a href='index.html' style='color:#c4a0e0'>← Zurück</a></p><h1>Impressum</h1>"
        f"<p><strong>{_esc(brand)}</strong><br/>{_esc(city or 'Deutschland')}</p>"
        f"<p>E-Mail: {_esc(email)}</p><p>Stand: 2026</p></body></html>",
        encoding="utf-8",
    )
    (dest / "datenschutz.html").write_text(
        f"<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'/><title>Datenschutz · {_esc(brand)}</title></head>"
        f"<body style='font-family:system-ui;background:#0a0710;color:#f6f0f8;padding:2rem'>"
        f"<p><a href='index.html' style='color:#c4a0e0'>← Zurück</a></p><h1>Datenschutz</h1>"
        f"<p>Daten nur zur Anfragen-/Bestellbearbeitung. Keine Kartenzahlung ohne Stripe Connect.</p>"
        f"<p>Stand: 2026</p></body></html>",
        encoding="utf-8",
    )
    if agb:
        (dest / "agb.html").write_text(
            f"<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'/><title>AGB · {_esc(brand)}</title></head>"
            f"<body style='font-family:system-ui;background:#0a0710;color:#f6f0f8;padding:2rem'>"
            f"<p><a href='index.html' style='color:#c4a0e0'>← Zurück</a></p><h1>AGB</h1>"
            f"<p>Bestellanfrage → Bestätigung → Zahlung nach Freischaltung.</p>"
            f"<p>Stand: 2026</p></body></html>",
            encoding="utf-8",
        )
