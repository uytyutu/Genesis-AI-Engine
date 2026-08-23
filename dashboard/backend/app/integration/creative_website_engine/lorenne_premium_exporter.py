# -*- coding: utf-8 -*-
"""Export LORENNE Premium Website + Shop from CreativeBusinessProject + cinematic keyframes.

Keyframe crossfade scroll-cinema (Premium path when i2v provider offline).
Does NOT patch legacy LORENNE HTML.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from app.factory.cinema_scroll import cinema_scroll_script
from app.integration.creative_website_engine.lorenne_sequence import (
    LORENNE_FRAMES,
    lorenne_storyboard,
)

ROOT = Path(__file__).resolve().parents[5]
CURSOR_ASSETS = Path.home() / ".cursor" / "projects" / "d-Games-Genesis-AI-Engine" / "assets"
OUT_WEB = (
    ROOT
    / "dashboard"
    / "frontend"
    / "public"
    / "package-previews"
    / "premium"
    / "lorenne"
)
OUT_SHOP = (
    ROOT
    / "dashboard"
    / "frontend"
    / "public"
    / "package-previews"
    / "premium"
    / "lorenne-shop"
)

# 20 coherent demo products — gift boxes niche
DEMO_PRODUCTS: list[dict[str, Any]] = [
    {"name": "Kraft Tanken Box", "cat": "Self Care", "price": 49.0, "frame": 10},
    {"name": "Zeit für Dich Box", "cat": "Self Care", "price": 54.0, "frame": 7},
    {"name": "Self Love Box", "cat": "Self Care", "price": 48.0, "frame": 9},
    {"name": "Beauty Box", "cat": "Beauty Gifts", "price": 51.0, "frame": 8},
    {"name": "Pink Glow Box", "cat": "Beauty Gifts", "price": 52.0, "frame": 13},
    {"name": "Sunday Reset Box", "cat": "Self Care", "price": 55.0, "frame": 14},
    {"name": "Birthday Soft Box", "cat": "Birthday", "price": 46.0, "frame": 11},
    {"name": "Birthday Sparkle Box", "cat": "Birthday", "price": 58.0, "frame": 12},
    {"name": "Romantic Evening Box", "cat": "Romantic", "price": 59.0, "frame": 10},
    {"name": "For You Box", "cat": "Romantic", "price": 47.0, "frame": 5},
    {"name": "Open When… Collection", "cat": "Special Moments", "price": 43.0, "frame": 16},
    {"name": "Neuer Lebensabschnitt Box", "cat": "Special Moments", "price": 52.0, "frame": 15},
    {"name": "Movie Night Box", "cat": "Seasonal", "price": 47.0, "frame": 9},
    {"name": "Winter Warmth Box", "cat": "Seasonal", "price": 53.0, "frame": 11},
    {"name": "Sakura Moment Box", "cat": "Seasonal", "price": 46.0, "frame": 12},
    {"name": "Premium Atelier Box", "cat": "Premium", "price": 79.0, "frame": 18},
    {"name": "Signature Lilac Box", "cat": "Premium", "price": 69.0, "frame": 2},
    {"name": "Danke Box", "cat": "Special Moments", "price": 39.0, "frame": 14},
    {"name": "Best Friends Box", "cat": "Birthday", "price": 45.0, "frame": 13},
    {"name": "Study Focus Box", "cat": "Self Care", "price": 42.0, "frame": 8},
    {"name": "Mama Box", "cat": "Special Moments", "price": 59.0, "frame": 10},
]


def _esc(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _collect_keyframes(seq_dir: Path) -> list[Path]:
    seq_dir.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    for i in range(1, 19):
        src = CURSOR_ASSETS / f"lorenne-f{i:02d}.png"
        if not src.is_file():
            # also try without zero pad
            alt = CURSOR_ASSETS / f"lorenne-f{i}.png"
            src = alt if alt.is_file() else src
        dest = seq_dir / f"f{i:03d}.jpg"
        if src.is_file():
            try:
                from PIL import Image

                im = Image.open(src).convert("RGB")
                im.save(dest, "JPEG", quality=88, optimize=True)
            except Exception:
                shutil.copy2(src, dest.with_suffix(".png"))
                dest = dest.with_suffix(".png")
        out.append(dest)
    return out


def export_lorenne_website(*, out_dir: Path | None = None) -> dict[str, Any]:
    dest = Path(out_dir) if out_dir else OUT_WEB
    seq = dest / "assets" / "seq"
    frames_paths = _collect_keyframes(seq)
    present = [p for p in frames_paths if p.is_file()]
    rel_frames = [f"assets/seq/{p.name}" for p in present]
    n = len(rel_frames)
    story = lorenne_storyboard()
    copies = [f["copy"] for f in LORENNE_FRAMES[:n]]

    # Build dual-buffer scroll cinema HTML (hot-dog family)
    imgs = "\n".join(
        f'      <img src="{_esc(rel_frames[0]) if i == 0 else ""}" data-src="{_esc(u)}" alt="" class="{"is-on" if i == 0 else ""}" />'
        for i, u in enumerate(rel_frames)
    )
    # simpler: all imgs with src
    imgs = "\n".join(
        f'      <img src="{_esc(u)}" alt="" class="{"is-on" if i == 0 else ""}" loading="lazy" />'
        for i, u in enumerate(rel_frames)
    )
    copies_js = json.dumps(copies, ensure_ascii=False)
    n_frames = max(n, 1)
    pin_h = f"calc(100vh + {n_frames} * 16vh)"

    categories = [
        ("Self Care", "Für Rituale und Ruhe."),
        ("Beauty Gifts", "Pflege zum Verschenken."),
        ("Birthday", "Für besondere Tage."),
        ("Romantic", "Für Momente zu zweit."),
        ("Premium", "Atelier-Auswahl."),
        ("Seasonal", "Zur Jahreszeit."),
        ("Special Moments", "Open when…"),
    ]
    cat_html = "".join(
        f'<article class="card"><h3>{_esc(t)}</h3><p>{_esc(d)}</p>'
        f'<a class="mini-cta" href="#shop-teaser">Kategorie ansehen →</a></article>'
        for t, d in categories
    )
    teaser = "".join(
        f'<article class="product"><img src="{_esc(rel_frames[min(p["frame"]-1, n-1)])}" alt="" />'
        f'<h3>{_esc(p["name"])}</h3><p class="price">{p["price"]:.0f} €</p></article>'
        for p in DEMO_PRODUCTS[:6]
    )

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>LORENNE · Premium Gift Boxes · Berlin</title>
  <meta name="description" content="LORENNE — hochwertige Geschenkboxen mit Beauty- und Self-Care. Elegant, emotional, premium. Berlin." />
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600&family=Outfit:wght@300;400;600&display=swap" rel="stylesheet" />
  <style>
    :root {{ --bg:#0a0710; --ink:#f6f0f8; --muted:#c9bfd4; --accent:#c4a0e0; --accent2:#6b3d8a; --line:rgba(255,255,255,.12); }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Outfit,system-ui,sans-serif; }}
    a {{ color:inherit; text-decoration:none; }}
    header.top {{ position:fixed; inset:0 0 auto; z-index:40; display:flex; justify-content:space-between; align-items:center;
      padding:.85rem 1.1rem; background:linear-gradient(to bottom,rgba(10,7,16,.88),transparent); }}
    header.top strong {{ font-family:"Cormorant Garamond",serif; font-size:1.2rem; letter-spacing:.04em; }}
    header.top nav {{ display:flex; gap:.75rem; align-items:center; flex-wrap:wrap; font-size:.8rem; color:var(--muted); }}
    .cta, .nav-cta, button.cta {{ display:inline-flex; align-items:center; justify-content:center; min-height:44px; padding:.7rem 1.2rem;
      border:0; border-radius:999px; background:linear-gradient(135deg,var(--accent),#e8d5f5); color:#1a1020; font-weight:600; cursor:pointer; font:inherit; }}
    header.top .nav-cta {{ min-height:36px; padding:.4rem .95rem; font-size:.78rem; }}
    .pin {{ position:relative; height:{pin_h}; }}
    .stage {{ position:sticky; top:0; height:100vh; overflow:hidden; background:#050308; }}
    .seq {{ position:absolute; inset:0; }}
    .seq img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; opacity:0; transition:opacity .06s linear; }}
    .seq img.is-on {{ opacity:1; }}
    .seq img.is-prev {{ opacity:.32; }}
    .vignette {{ position:absolute; inset:0; pointer-events:none;
      background:radial-gradient(ellipse at 50% 40%,transparent 12%,rgba(0,0,0,.58) 78%),linear-gradient(to top,rgba(0,0,0,.88),transparent 46%); }}
    .hud {{ position:absolute; inset:0; z-index:5; display:flex; flex-direction:column; justify-content:flex-end;
      padding:clamp(1.2rem,4vw,3rem); pointer-events:none; }}
    .hud > * {{ pointer-events:auto; }}
    .eyebrow {{ letter-spacing:.28em; text-transform:uppercase; font-size:.7rem; color:var(--accent); margin:0 0 .5rem; text-shadow:0 1px 8px rgba(0,0,0,.8); }}
    h1 {{ font-family:"Cormorant Garamond",serif; font-size:clamp(2.3rem,6.5vw,4.6rem); line-height:.95; margin:0 0 .55rem; max-width:12ch;
      text-shadow:0 2px 18px rgba(0,0,0,.75); }}
    .beat-line {{ color:#efe6f6; font-size:clamp(1.05rem,2.4vw,1.35rem); max-width:28rem; min-height:2.8em; margin:0 0 1rem; line-height:1.4;
      text-shadow:0 1px 10px rgba(0,0,0,.85); }}
    .frame-meter {{ color:rgba(255,255,255,.55); font-size:.72rem; letter-spacing:.12em; margin:0 0 .8rem; }}
    .progress {{ position:absolute; top:0; left:0; height:3px; width:100%; transform:scaleX(0); transform-origin:left center; background:linear-gradient(90deg,var(--accent2),var(--accent)); z-index:8; will-change:transform; }}
    .hint {{ position:absolute; right:1.1rem; bottom:1rem; z-index:6; color:var(--muted); font-size:.72rem; letter-spacing:.1em; }}
    .section {{ max-width:68rem; margin:0 auto; padding:4.2rem 1.25rem; scroll-margin-top:5rem; }}
    .section h2 {{ font-family:"Cormorant Garamond",serif; font-size:clamp(2rem,4vw,3rem); margin:.3rem 0 1rem; }}
    .lead {{ color:var(--muted); font-size:1.05rem; line-height:1.7; max-width:44rem; }}
    .grid-cards {{ display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); margin-top:1.4rem; }}
    .card {{ border:1px solid var(--line); border-radius:1rem; padding:1rem; background:rgba(255,255,255,.03); }}
    .card h3 {{ margin:0 0 .35rem; font-size:1.02rem; }}
    .card p {{ margin:0; color:var(--muted); font-size:.9rem; }}
    .mini-cta {{ display:inline-block; margin-top:.7rem; color:var(--accent); font-size:.85rem; }}
    .product-grid {{ display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); }}
    .product {{ border:1px solid var(--line); border-radius:1rem; overflow:hidden; background:rgba(255,255,255,.03); }}
    .product img {{ width:100%; aspect-ratio:1; object-fit:cover; display:block; }}
    .product h3 {{ margin:.75rem .85rem .2rem; font-size:1rem; }}
    .product .price {{ margin:0 .85rem .7rem; color:var(--accent); font-weight:600; }}
    .contact-shell {{ display:grid; gap:1.2rem; grid-template-columns:1.05fr .95fr; margin-top:1.4rem; }}
    @media (max-width:860px) {{ .contact-shell {{ grid-template-columns:1fr; }} .hint {{ display:none; }} header.top nav a:not(.nav-cta) {{ display:none; }} .pin {{ height:calc(100vh + {n_frames} * 12vh); }} }}
    .contact-panel {{ border:1px solid var(--line); border-radius:1.15rem; padding:1.15rem; background:rgba(255,255,255,.03); }}
    form.msg {{ display:grid; gap:.65rem; }}
    form.msg label {{ font-size:.75rem; color:var(--muted); }}
    form.msg input, form.msg textarea {{ width:100%; border-radius:.7rem; border:1px solid var(--line); background:#120c18; color:var(--ink); padding:.7rem .8rem; font:inherit; }}
    .review {{ border:1px solid var(--line); border-radius:1rem; padding:1rem; background:rgba(255,255,255,.03); }}
    .review .stars {{ color:var(--accent); letter-spacing:.06em; }}
    .demo-tag {{ display:inline-block; margin-top:.45rem; font-size:.65rem; letter-spacing:.12em; text-transform:uppercase; color:#e8b4ff; border:1px solid rgba(196,160,224,.35); padding:.15rem .45rem; border-radius:999px; }}
    footer.site {{ border-top:1px solid var(--line); padding:1.4rem 1.2rem 2.4rem; color:var(--muted); font-size:.8rem; text-align:center; }}
  </style>
</head>
<body>
  <header class="top">
    <strong>LORENNE</strong>
    <nav>
      <a href="#about">Über uns</a>
      <a href="#categories">Kategorien</a>
      <a href="#shop-teaser">Boxen</a>
      <a href="#reviews">Bewertungen</a>
      <a href="#kontakt">Kontakt</a>
      <a class="nav-cta" href="#kontakt">Box wählen</a>
    </nav>
  </header>

  <div class="pin" id="cinemaPin">
    <div class="stage">
      <div class="progress" id="prog"></div>
      <div class="seq" id="seq">{imgs}
      </div>
      <div class="vignette"></div>
      <div class="hud">
        <p class="eyebrow">Premium Gift Boxes · Berlin</p>
        <h1>LORENNE</h1>
        <p class="beat-line" id="beatLine">{_esc(copies[0] if copies else "Scroll — die Szene beginnt.")}</p>
        <p class="frame-meter" id="meter">FRAME 001 / {n_frames:03d}</p>
        <a class="cta" href="#kontakt">Box wählen</a>
      </div>
      <p class="hint">SCROLL ↓</p>
    </div>
  </div>

  <section class="section" id="about">
    <p class="eyebrow">Über LORENNE</p>
    <h2>Geschenkboxen mit Seele</h2>
    <p class="lead">
      LORENNE kuratiert hochwertige Geschenkboxen mit Beauty- und Self-Care-Momenten —
      für Partner, Freundinnen, Geburtstage und besondere Augenblicke.
      Elegant. Emotional. Premium. Berlin.
    </p>
  </section>

  <section class="section" id="categories">
    <h2>Welche Box passt zu Ihnen?</h2>
    <div class="grid-cards">{cat_html}</div>
  </section>

  <section class="section" id="shop-teaser">
    <h2>Featured Gifts</h2>
    <p class="lead">Eine Auswahl aus dem Premium-Shop — vollständiger Katalog im Online-Shop.</p>
    <div class="product-grid" style="margin-top:1.4rem">{teaser}</div>
    <p style="margin-top:1.2rem"><a class="cta" href="./../lorenne-shop/index.html">Zum Online-Shop →</a></p>
  </section>

  <section class="section" id="reviews">
    <h2>Kundenbewertungen</h2>
    <div class="grid-cards">
      <article class="review"><p class="stars">★★★★★</p><p>Die Verpackung allein war schon ein Moment.</p><span class="demo-tag">DEMO REVIEW</span></article>
      <article class="review"><p class="stars">★★★★★</p><p>Genau das richtige Geschenk — elegant und persönlich.</p><span class="demo-tag">DEMO REVIEW</span></article>
      <article class="review"><p class="stars">★★★★☆</p><p>Schöne Zusammenstellung, soft lilac Look.</p><span class="demo-tag">DEMO REVIEW</span></article>
    </div>
  </section>

  <section class="section" id="kontakt">
    <h2>Kontakt</h2>
    <div class="contact-shell">
      <div class="contact-panel">
        <p class="lead">Berlin · LORENNE Gift Boxes</p>
        <p class="lead" style="margin-top:.6rem">E-Mail und Telefon erscheinen hier, sobald Sie sie im Workspace hinterlegen — keine erfundenen Konten.</p>
      </div>
      <div class="contact-panel">
        <form class="msg" onsubmit="event.preventDefault(); this.querySelector('.ok').style.display='block';">
          <label>Name<input name="name" required autocomplete="name" /></label>
          <label>Email<input type="email" name="email" required autocomplete="email" /></label>
          <label>Telefon<input type="tel" name="phone" autocomplete="tel" /></label>
          <label>Nachricht<textarea name="msg" rows="4" required></textarea></label>
          <button class="cta" type="submit">Nachricht senden</button>
          <p class="ok" style="display:none;color:#b8f0c8">Danke — Nachricht (Demo) erfasst.</p>
        </form>
      </div>
    </div>
  </section>

  <footer class="site">
    LORENNE · Premium Gift Boxes · Berlin · seit 2026<br />
    <a href="impressum.html">Impressum</a> ·
    <a href="datenschutz.html">Datenschutz</a> ·
    <a href="#about">Über uns</a> ·
    <a href="./../lorenne-shop/index.html">Online-Shop</a>
  </footer>

  <script>
  {cinema_scroll_script(copies_js=copies_js)}
  </script>
</body>
</html>
"""
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "index.html").write_text(html, encoding="utf-8")
    for name, body in (
        (
            "impressum.html",
            "<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'/><title>Impressum · LORENNE</title></head>"
            "<body style='font-family:system-ui;background:#0a0710;color:#f6f0f8;padding:2rem'>"
            "<p><a href='index.html' style='color:#c4a0e0'>← Website</a></p><h1>Impressum</h1>"
            "<p><strong>LORENNE</strong><br/>Premium Gift Boxes<br/>Berlin</p>"
            "<p>Vertreten durch: Svitlana Bulhakova</p><p>Stand: 2026</p></body></html>",
        ),
        (
            "datenschutz.html",
            "<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'/><title>Datenschutz · LORENNE</title></head>"
            "<body style='font-family:system-ui;background:#0a0710;color:#f6f0f8;padding:2rem'>"
            "<p><a href='index.html' style='color:#c4a0e0'>← Website</a></p><h1>Datenschutz</h1>"
            "<p>Kontaktformular-Daten nur zur Anfragenbearbeitung. Stand: 2026</p></body></html>",
        ),
    ):
        (dest / name).write_text(body, encoding="utf-8")
    (dest / "manifest.json").write_text(
        json.dumps(
            {
                "brand": "LORENNE",
                "from": "CreativeBusinessProject",
                "frames": n,
                "delivery": story.get("delivery"),
                "quality_state": "REVIEW_REQUIRED",
                "do_not_patch_legacy": True,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {"ok": True, "path": str(dest), "frames": n, "kind": "website"}


def export_lorenne_shop(*, out_dir: Path | None = None, web_seq: Path | None = None) -> dict[str, Any]:
    dest = Path(out_dir) if out_dir else OUT_SHOP
    dest.mkdir(parents=True, exist_ok=True)
    assets = dest / "assets" / "products"
    assets.mkdir(parents=True, exist_ok=True)
    src_seq = Path(web_seq) if web_seq else OUT_WEB / "assets" / "seq"
    products_html = []
    for i, p in enumerate(DEMO_PRODUCTS):
        src = src_seq / f"f{p['frame']:03d}.jpg"
        if not src.is_file():
            src = src_seq / f"f{p['frame']:03d}.png"
        local = assets / f"p{i+1:02d}{src.suffix if src.is_file() else '.jpg'}"
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

    cats = sorted({p["cat"] for p in DEMO_PRODUCTS})
    cat_nav = "".join(f'<button type="button" class="chip" data-cat="{_esc(c)}">{_esc(c)}</button>' for c in ["Alle", *cats])

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>LORENNE Shop · Premium Gift Boxes</title>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600&family=Outfit:wght@300;400;600&display=swap" rel="stylesheet" />
  <style>
    :root {{ --bg:#0a0710; --ink:#f6f0f8; --muted:#c9bfd4; --accent:#c4a0e0; --line:rgba(255,255,255,.12); }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Outfit,system-ui,sans-serif; }}
    a {{ color:inherit; text-decoration:none; }}
    header {{ position:sticky; top:0; z-index:20; display:flex; justify-content:space-between; align-items:center; gap:1rem; flex-wrap:wrap;
      padding:.85rem 1.1rem; background:rgba(10,7,16,.92); border-bottom:1px solid var(--line); backdrop-filter:blur(8px); }}
    header strong {{ font-family:"Cormorant Garamond",serif; font-size:1.25rem; }}
    .cta {{ border:0; border-radius:999px; padding:.65rem 1.1rem; background:linear-gradient(135deg,var(--accent),#e8d5f5); color:#1a1020; font-weight:600; cursor:pointer; font:inherit; min-height:44px; }}
    .hero {{ position:relative; min-height:70vh; display:grid; place-items:end start; padding:2rem 1.25rem 3rem;
      background:url('../lorenne/assets/seq/f010.jpg') center/cover; }}
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
    .product img {{ width:100%; aspect-ratio:1; object-fit:cover; }}
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
    .cta.ghost {{ background:transparent; color:var(--ink); border:1px solid var(--line); }}
    footer {{ border-top:1px solid var(--line); padding:1.5rem; text-align:center; color:var(--muted); font-size:.8rem; }}
    footer a {{ color:var(--accent); }}
  </style>
</head>
<body>
  <header>
    <strong>LORENNE Shop</strong>
    <nav style="display:flex;gap:.75rem;align-items:center;flex-wrap:wrap">
      <a href="../lorenne/index.html">Website</a>
      <a href="#catalog">Katalog</a>
      <a href="impressum.html">Impressum</a>
      <button type="button" class="cta" id="cartBtn">Warenkorb (<span id="cartCount">0</span>)</button>
    </nav>
  </header>
  <section class="hero">
    <div class="hero-inner">
      <p class="muted" style="letter-spacing:.2em;text-transform:uppercase;font-size:.7rem;color:var(--accent)">Desire → Product → Purchase</p>
      <h1>Geschenkboxen mit Seele</h1>
      <p>Premium Online-Shop — dieselben Boxen, dieselbe visuelle Welt wie die Website.</p>
      <p style="margin-top:1rem"><a class="cta" href="#catalog">Katalog öffnen</a></p>
    </div>
  </section>
  <main class="wrap" id="catalog">
    <h2 style="font-family:'Cormorant Garamond',serif;font-size:2rem;margin:0">Katalog · {len(DEMO_PRODUCTS)} Boxen</h2>
    <div class="chips" id="chips">{cat_nav}</div>
    <div class="grid" id="grid">{''.join(products_html)}</div>
  </main>
  <div class="drawer-bg" id="drawerBg" aria-hidden="true"></div>
  <aside class="drawer" id="cartDrawer" aria-label="Warenkorb und Kasse">
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
      <label>Land
        <select name="country"><option value="DE" selected>Deutschland</option><option value="AT">Österreich</option><option value="CH">Schweiz</option></select>
      </label>
      <label>Versandart
        <select name="shipping" id="shipping">
          <option value="dhl_std" data-fee="4.90">DHL Standard — 4,90 €</option>
          <option value="dhl_exp" data-fee="9.90">DHL Express — 9,90 €</option>
          <option value="pickup" data-fee="0">Abholung Berlin — 0 €</option>
        </select>
      </label>
      <p class="muted">Versand: <strong id="shipFee">4,90</strong> € · Gesamt: <strong id="grandTotal">0</strong> €</p>
      <p class="warn" id="payNote">
        Zahlung über den Shop der Händlerin (Stripe Connect). Status: <strong>Nicht verbunden</strong>.
        Bestellung wird als Anfrage gespeichert — Zahlungslink folgt nach Aktivierung.
      </p>
      <label>Hinweis (optional)<textarea name="note" rows="2"></textarea></label>
      <button type="submit" class="cta" style="width:100%;margin-top:.8rem">Bestellung absenden</button>
      <button type="button" class="cta ghost" id="backCart" style="width:100%;margin-top:.5rem">Zurück zum Warenkorb</button>
    </form>
    <div id="doneStep" style="display:none">
      <p class="ok">Vielen Dank — Bestellung <strong id="orderId"></strong> wurde erfasst.</p>
      <p class="muted" style="margin-top:.6rem">Bestätigung per E-Mail, sobald Zahlung freigeschaltet ist.</p>
      <button type="button" class="cta" id="doneClose" style="width:100%;margin-top:1rem">Weiter einkaufen</button>
    </div>
  </aside>
  <footer>
    LORENNE · Premium Gift Boxes · Berlin · seit 2026<br />
    <a href="impressum.html">Impressum</a> ·
    <a href="datenschutz.html">Datenschutz</a> ·
    <a href="agb.html">AGB</a> ·
    <a href="../lorenne/index.html">Website</a>
  </footer>
  <script>
  (function(){{
    var KEY = 'lorenne_shop_cart_v1';
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
      if (!cart.length) {{
        list.innerHTML = '<p class="muted">Ihr Warenkorb ist leer.</p>';
      }} else {{
        list.innerHTML = cart.map(function(x, i){{
          return '<div class="cart-line"><span>'+x.name+'</span><span>'+money(x.price)+' € <button type="button" data-i="'+i+'" class="rm" style="margin-left:.4rem;border:0;background:transparent;color:#e8b4ff;cursor:pointer">✕</button></span></div>';
        }}).join('');
      }}
      document.getElementById('cartSum').textContent = money(subtotal());
      document.getElementById('grandTotal').textContent = money(subtotal() + shipFee());
      document.getElementById('shipFee').textContent = money(shipFee());
      list.querySelectorAll('.rm').forEach(function(btn){{
        btn.addEventListener('click', function(){{
          cart.splice(parseInt(btn.getAttribute('data-i'),10), 1);
          save(); renderCart();
        }});
      }});
    }}
    chips.forEach(function(ch){{
      ch.addEventListener('click', function(){{
        chips.forEach(function(c){{ c.classList.remove('on'); }});
        ch.classList.add('on');
        var cat = ch.getAttribute('data-cat');
        products.forEach(function(p){{
          var pc = p.querySelector('.cat').textContent;
          p.style.display = (cat === 'Alle' || pc === cat) ? '' : 'none';
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
        document.getElementById('drawerTitle').textContent = 'Warenkorb';
        openDrawer();
      }});
    }});
    document.getElementById('cartBtn').addEventListener('click', function(){{
      document.getElementById('cartStep').style.display = '';
      document.getElementById('checkoutStep').style.display = 'none';
      document.getElementById('doneStep').style.display = 'none';
      document.getElementById('drawerTitle').textContent = 'Warenkorb';
      renderCart(); openDrawer();
    }});
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
        id: 'LRN-' + Date.now().toString(36).toUpperCase(),
        created_at: new Date().toISOString(),
        items: cart.slice(),
        subtotal: subtotal(),
        shipping_fee: shipFee(),
        shipping: fd.get('shipping'),
        total: subtotal() + shipFee(),
        customer: {{
          name: fd.get('name'), email: fd.get('email'), phone: fd.get('phone'),
          street: fd.get('street'), zip: fd.get('zip'), city: fd.get('city'), country: fd.get('country'),
          note: fd.get('note')
        }},
        payment_status: 'awaiting_merchant_connect',
        payment_note: 'Stripe Connect not connected — order saved as request'
      }};
      try {{
        var hist = JSON.parse(localStorage.getItem('lorenne_shop_orders_v1') || '[]');
        hist.unshift(order);
        localStorage.setItem('lorenne_shop_orders_v1', JSON.stringify(hist.slice(0, 40)));
      }} catch (e) {{}}
      cart = []; save(); renderCart();
      document.getElementById('checkoutStep').style.display = 'none';
      document.getElementById('doneStep').style.display = '';
      document.getElementById('orderId').textContent = order.id;
      document.getElementById('drawerTitle').textContent = 'Bestätigt';
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
    for name, body in (
        (
            "impressum.html",
            "<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/><title>Impressum · LORENNE</title></head>"
            "<body style='font-family:system-ui;background:#0a0710;color:#f6f0f8;padding:2rem'>"
            "<p><a href='index.html' style='color:#c4a0e0'>← Shop</a></p><h1>Impressum</h1>"
            "<p><strong>LORENNE</strong><br/>Premium Gift Boxes<br/>Berlin, Deutschland</p>"
            "<p>Vertreten durch: Svitlana Bulhakova</p>"
            "<p>E-Mail: im Workspace hinterlegen.</p><p>Stand: 2026</p></body></html>",
        ),
        (
            "datenschutz.html",
            "<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'/><title>Datenschutz · LORENNE</title></head>"
            "<body style='font-family:system-ui;background:#0a0710;color:#f6f0f8;padding:2rem'>"
            "<p><a href='index.html' style='color:#c4a0e0'>← Shop</a></p><h1>Datenschutzerklärung</h1>"
            "<p>Bestelldaten nur zur Bearbeitung der Anfrage. Keine Kartenzahlung solange Stripe Connect nicht verbunden ist.</p>"
            "<p>Stand: 2026</p></body></html>",
        ),
        (
            "agb.html",
            "<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'/><title>AGB · LORENNE</title></head>"
            "<body style='font-family:system-ui;background:#0a0710;color:#f6f0f8;padding:2rem'>"
            "<p><a href='index.html' style='color:#c4a0e0'>← Shop</a></p><h1>AGB</h1>"
            "<p>Bestellanfrage → Bestätigung durch LORENNE → Zahlung nach Freischaltung.</p>"
            "<p>Stand: 2026</p></body></html>",
        ),
    ):
        (dest / name).write_text(body, encoding="utf-8")
    (dest / "catalog.json").write_text(
        json.dumps({"products": DEMO_PRODUCTS, "demo": True}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"ok": True, "path": str(dest), "products": len(DEMO_PRODUCTS), "kind": "shop"}


def export_lorenne_premium_pair() -> dict[str, Any]:
    web = export_lorenne_website()
    shop = export_lorenne_shop()
    return {
        "website": web,
        "shop": shop,
        "quality_state": "REVIEW_REQUIRED",
        "note": "Keyframe scroll-cinema composed. Image-to-video clips still pending provider. Do not mark READY until visual QA PASS.",
    }


if __name__ == "__main__":
    print(json.dumps(export_lorenne_premium_pair(), ensure_ascii=False, indent=2))
