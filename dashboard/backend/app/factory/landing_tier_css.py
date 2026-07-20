"""Tier design-system CSS for Path A Factory ZIP landings."""

from __future__ import annotations

from typing import Protocol


class _Style(Protocol):
    primary: str
    primary_dark: str
    accent: str
    hero_gradient: str


def tier_stylesheet(tier: str, style: _Style) -> str:
    """Return CSS differentiated by package tier (basic / business / premium)."""
    t = tier if tier in ("basic", "business", "premium") else "basic"
    p, pd, acc, grad = style.primary, style.primary_dark, style.accent, style.hero_gradient

    base = f"""
    :root {{
      --p: {p}; --pd: {pd}; --acc: {acc};
      --ink: #0f172a; --muted: #64748b; --line: #e2e8f0; --surface: #f8fafc;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ color: var(--ink); line-height: 1.65; }}
    a {{ color: inherit; }}
    .topbar {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 0.75rem 1.5rem; gap: 1rem; position: sticky; top: 0; z-index: 10;
    }}
    .brand {{ display: flex; align-items: center; gap: 0.75rem; }}
    .brand img {{ height: 40px; width: auto; max-width: 140px; object-fit: contain; background: #fff; border-radius: 6px; padding: 2px 6px; }}
    .brand .logo-fallback {{
      width: 40px; height: 40px; border-radius: 8px; background: var(--acc); color: #0f172a;
      display: grid; place-items: center; font-weight: 800; font-size: 0.85rem;
    }}
    .topbar-links {{ display: flex; gap: 0.85rem; align-items: center; flex-wrap: wrap; }}
    .topbar-links a {{ text-decoration: none; font-weight: 600; font-size: 0.9rem; }}
    .hero {{
      position: relative; color: #fff; text-align: center; overflow: hidden;
      background: {grad};
      background-size: cover; background-position: center;
    }}
    .hero.has-photo {{
      background-image: linear-gradient(120deg, rgba(15,23,42,.72), rgba(15,23,42,.45)), url("assets/hero.jpg");
      background-size: cover; background-position: center;
    }}
    .hero-inner {{ position: relative; z-index: 1; max-width: 48rem; margin: 0 auto; }}
    .hero h1 {{ font-weight: 800; letter-spacing: -0.02em; margin-bottom: 1rem; }}
    .hero p.lead {{ opacity: 0.95; margin: 0 auto 1.5rem; }}
    .trust-row {{ display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center; margin-bottom: 2rem; }}
    .trust-pill {{
      background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.25);
      padding: 0.35rem 0.85rem; border-radius: 999px; font-size: 0.8rem;
    }}
    .hero-ctas {{ display: flex; flex-wrap: wrap; gap: 0.75rem; justify-content: center; }}
    .btn {{
      display: inline-block; background: var(--acc); color: #0f172a; font-weight: 700;
      padding: 0.875rem 2rem; border-radius: 999px; text-decoration: none;
      box-shadow: 0 8px 24px rgba(0,0,0,0.2); transition: transform .2s, box-shadow .2s;
    }}
    .btn:hover {{ transform: translateY(-1px); }}
    .btn-wa {{ background: #25d366; color: #052e16; }}
    .btn-reviews {{ background: transparent; color: #fff; border: 2px solid rgba(255,255,255,0.85); }}
    .wa-btn {{ color: #15803d; font-weight: 700; }}
    .section {{ padding: 3.5rem 1.5rem; max-width: 960px; margin: 0 auto; }}
    .section h2 {{ font-size: 1.75rem; margin-bottom: 1.25rem; color: var(--pd); }}
    .services {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); list-style: none; }}
    .service-card {{
      background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 1.25rem;
      transition: transform .2s, box-shadow .2s;
    }}
    .service-card h3 {{ font-size: 1.05rem; margin-bottom: 0.5rem; color: var(--pd); }}
    .service-desc {{ font-size: 0.92rem; color: #475569; }}
    .service-card:hover {{ transform: translateY(-2px); box-shadow: 0 12px 24px rgba(0,0,0,0.08); }}
    .catalog-tools {{
      display: flex; flex-wrap: wrap; gap: 0.75rem; margin: 1rem 0 1.5rem;
    }}
    .catalog-tools input, .catalog-tools select {{
      padding: 0.65rem 0.85rem; border: 1px solid var(--line); border-radius: 8px;
      font: inherit; min-width: 12rem;
    }}
    .catalog-grid {{
      display: grid; gap: 1.25rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }}
    .product-card {{
      background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 1rem;
      display: flex; flex-direction: column; gap: 0.5rem;
    }}
    .product-card.rich {{ padding: 1.35rem; box-shadow: 0 12px 32px rgba(15,23,42,0.08); }}
    .product-card img, .product-ph {{
      width: 100%; height: 160px; object-fit: cover; border-radius: 8px; background: var(--surface);
    }}
    .product-card h3 {{ font-size: 1.05rem; color: var(--pd); }}
    .product-card .price {{ font-weight: 700; color: var(--p); }}
    .product-card .summary {{ color: var(--muted); font-size: 0.92rem; flex: 1; }}
    .btn-catalog {{
      margin-top: 0.5rem; border: 0; cursor: pointer; background: var(--acc); color: #0f172a;
      font-weight: 700; padding: 0.65rem 1rem; border-radius: 999px; font: inherit;
    }}
    .catalog-cart {{
      margin-top: 1.5rem; padding: 1rem 1.25rem; border: 1px dashed var(--line);
      border-radius: 12px; background: var(--surface);
    }}
    .catalog-cart ul {{ margin: 0.5rem 0 1rem 1.25rem; }}
    .about {{ background: #f1f5f9; }}
    .benefits ul {{ list-style: none; display: grid; gap: 0.75rem; }}
    .benefits li {{ padding-left: 1.5rem; position: relative; }}
    .benefits li::before {{ content: "✓"; position: absolute; left: 0; color: var(--p); font-weight: 700; }}
    .muted {{ color: var(--muted); margin-bottom: 1rem; }}
    .contact-grid {{ display: grid; gap: 0.5rem; }}
    .contact-form {{ display: grid; gap: 0.75rem; max-width: 480px; margin-top: 1.25rem; }}
    .contact-form label {{ display: grid; gap: 0.35rem; font-weight: 600; font-size: 0.9rem; }}
    .contact-form input, .contact-form textarea {{
      padding: 0.65rem 0.75rem; border-radius: 8px; border: 1px solid #cbd5e1; font: inherit;
    }}
    .contact-form button {{
      justify-self: start; background: var(--p); color: #fff; border: 0;
      padding: 0.75rem 1.5rem; border-radius: 999px; font-weight: 700; cursor: pointer;
    }}
    .calculator {{ background: #fff; border-top: 1px solid var(--line); }}
    .calc-grid {{ display: grid; gap: 1rem; max-width: 400px; }}
    .calc-grid label {{ display: flex; flex-direction: column; gap: 0.5rem; font-weight: 600; }}
    .calc-grid select, .calc-grid input {{ padding: 0.5rem; border-radius: 8px; border: 1px solid #cbd5e1; }}
    .calc-result {{ font-size: 1.25rem; margin-top: 0.5rem; }}
    .testimonials {{ background: var(--surface); }}
    .testimonial-grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
    .testimonial-card {{ background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 1.25rem; }}
    .testimonial-card cite {{ display: block; margin-top: 0.75rem; font-size: 0.875rem; color: var(--muted); }}
    .maps-frame {{ border-radius: 12px; overflow: hidden; border: 1px solid var(--line); aspect-ratio: 16/9; }}
    .maps-frame iframe {{ width: 100%; height: 100%; border: 0; }}
    .maps-actions {{ display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1rem; align-items: center; }}
    .maps-actions .chip {{ font-size: 0.85rem; color: var(--muted); }}
    .btn-route {{
      display: inline-block; background: var(--p); color: #fff; font-weight: 700;
      padding: 0.65rem 1.25rem; border-radius: 999px; text-decoration: none;
    }}
    .trust-strip {{
      display: flex; flex-wrap: wrap; gap: 0.75rem; justify-content: center;
      padding: 0.85rem 1rem; background: #0f172a; color: #e2e8f0; font-size: 0.85rem; font-weight: 600;
    }}
    .info-bar {{
      display: flex; flex-wrap: wrap; gap: 1.25rem; justify-content: center;
      padding: 0.9rem 1.25rem; background: rgba(15,23,42,0.92); color: #fff; font-size: 0.9rem;
    }}
    .info-bar strong {{ color: var(--acc); }}
    .mid-cta {{
      text-align: center; padding: 2.75rem 1.5rem; background: linear-gradient(135deg, var(--pd), var(--p)); color: #fff;
    }}
    .mid-cta h2 {{ color: #fff; margin-bottom: 1rem; font-size: 1.6rem; }}
    .faq-list {{ display: grid; gap: 0.85rem; }}
    .faq-item {{ background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 1rem 1.15rem; }}
    .faq-item h3 {{ font-size: 1rem; margin-bottom: 0.35rem; color: var(--pd); }}
    .faq-item p {{ color: #475569; font-size: 0.95rem; }}
    .process-grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }}
    .process-card {{
      border: 1px solid var(--line); border-radius: 12px; padding: 1.25rem; background: #fff;
    }}
    .process-card .n {{
      width: 2rem; height: 2rem; border-radius: 999px; background: var(--p); color: #fff;
      display: grid; place-items: center; font-weight: 800; margin-bottom: 0.75rem; font-size: 0.9rem;
    }}
    .cert-row {{ display: flex; flex-wrap: wrap; gap: 0.6rem; margin-top: 1rem; }}
    .cert-badge {{
      border: 1px solid var(--line); background: #fff; border-radius: 999px;
      padding: 0.4rem 0.85rem; font-size: 0.8rem; font-weight: 600; color: var(--pd);
    }}
    .stats {{
      display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;
      padding: 2.5rem 1.5rem; background: #0f172a; color: #fff; text-align: center;
    }}
    .stat strong {{ display: block; font-size: clamp(1.75rem, 4vw, 2.5rem); letter-spacing: -0.03em; color: var(--acc); }}
    .stat span {{ font-size: 0.85rem; color: #94a3b8; }}
    .showcase {{ max-width: 1100px; }}
    .showcase-grid {{ display: grid; gap: 1rem; grid-template-columns: 1.6fr 1fr 1fr; }}
    .showcase-panel {{
      border-radius: 16px; min-height: 220px; background-size: cover; background-position: center;
      position: relative; overflow: hidden; box-shadow: 0 16px 40px rgba(15,23,42,0.18);
      transition: transform .25s ease;
    }}
    .showcase-panel:hover {{ transform: scale(1.015); }}
    .showcase-panel.main {{
      background-image: linear-gradient(180deg, transparent 40%, rgba(15,23,42,.7)), url("assets/hero.jpg");
      min-height: 320px;
    }}
    .showcase-panel.tone-a {{ background: linear-gradient(145deg, var(--pd), var(--p)); }}
    .showcase-panel.tone-b {{ background: linear-gradient(145deg, #0f172a, var(--pd)); }}
    .showcase-panel .cap {{
      position: absolute; left: 1rem; bottom: 1rem; color: #fff; font-weight: 700; font-size: 0.95rem;
    }}
    .client-gallery-grid {{
      display: grid; gap: 0.85rem;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    }}
    .client-photo {{
      margin: 0; border-radius: 12px; overflow: hidden;
      background: #e2e8f0; aspect-ratio: 4 / 3;
    }}
    .client-photo img {{
      width: 100%; height: 100%; object-fit: cover; display: block;
    }}
    footer {{ text-align: center; padding: 2rem; font-size: 0.875rem; background: #0f172a; color: #cbd5e1; }}
    @keyframes heroIn {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: none; }} }}
    .hero-anim {{ animation: heroIn .7s ease both; }}
    .hero-anim-d1 {{ animation-delay: .12s; }}
    .hero-anim-d2 {{ animation-delay: .24s; }}
    @media (max-width: 720px) {{
      .showcase-grid {{ grid-template-columns: 1fr; }}
      .stats {{ grid-template-columns: 1fr; }}
      .hero {{ padding: 3rem 1rem 4rem !important; }}
      .section {{ padding: 2.5rem 1rem; }}
      body[data-tier="business"] .hero-inner,
      body[data-tier="premium"] .hero-inner {{ padding: 0 1rem; }}
    }}
"""

    if t == "basic":
        return base + """
    body[data-tier="basic"] { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; }
    body[data-tier="basic"] .topbar {
      background: rgba(255,255,255,0.92); color: var(--ink); backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--line);
    }
    body[data-tier="basic"] .topbar a { color: var(--pd); }
    body[data-tier="basic"] .hero {
      min-height: 62vh; display: grid; place-items: center; padding: 4.5rem 1.5rem 5rem;
    }
    body[data-tier="basic"] .hero h1 { font-size: clamp(2rem, 5vw, 3.1rem); max-width: 42rem; margin-inline: auto; }
    body[data-tier="basic"] .hero p.lead { font-size: 1.15rem; max-width: 34rem; }
    body[data-tier="basic"] .section { padding-top: 4rem; padding-bottom: 4rem; }
    body[data-tier="basic"] .service-card {
      background: #fff; border-radius: 14px;
      box-shadow: 0 10px 28px rgba(15,23,42,0.06);
    }
    body[data-tier="basic"] .process-card { border-radius: 14px; }
    body[data-tier="basic"] .mid-cta { margin: 0 1rem; border-radius: 16px; }
"""

    if t == "business":
        return base + """
    body[data-tier="business"] { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; }
    body[data-tier="business"] .topbar { background: rgba(15,23,42,0.96); color: #fff; }
    body[data-tier="business"] .topbar a { color: var(--acc); }
    body[data-tier="business"] .hero { padding: 4.25rem 1.5rem 3.5rem; text-align: left; }
    body[data-tier="business"] .hero-inner { margin: 0; max-width: 40rem; padding: 0 1.5rem 0 8vw; }
    body[data-tier="business"] .hero h1 { font-size: clamp(1.9rem, 4vw, 2.75rem); margin-inline: 0; }
    body[data-tier="business"] .hero p.lead { margin-inline: 0; font-size: 1.05rem; max-width: 34rem; }
    body[data-tier="business"] .trust-row,
    body[data-tier="business"] .hero-ctas { justify-content: flex-start; }
    body[data-tier="business"] .service-card {
      border-left: 3px solid var(--p); border-radius: 8px; box-shadow: 0 4px 14px rgba(15,23,42,0.06);
    }
"""

    return base + """
    body[data-tier="premium"] { font-family: Georgia, "Times New Roman", serif; }
    body[data-tier="premium"] .topbar {
      background: rgba(15,23,42,0.55); color: #fff; backdrop-filter: blur(14px);
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    body[data-tier="premium"] .topbar a { color: #fff; }
    body[data-tier="premium"] .topbar strong,
    body[data-tier="premium"] .btn,
    body[data-tier="premium"] .section h2,
    body[data-tier="premium"] .service-card h3,
    body[data-tier="premium"] .faq-item h3,
    body[data-tier="premium"] .process-card,
    body[data-tier="premium"] .contact-form,
    body[data-tier="premium"] .info-bar,
    body[data-tier="premium"] .trust-strip,
    body[data-tier="premium"] .stat span,
    body[data-tier="premium"] .topbar-links,
    body[data-tier="premium"] .hero p.lead {
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    }
    body[data-tier="premium"] .hero {
      min-height: 88vh; display: grid; place-items: end center; padding: 0 1.5rem 4.5rem; text-align: left;
    }
    body[data-tier="premium"] .hero.has-photo {
      background-image: linear-gradient(180deg, rgba(15,23,42,.25) 10%, rgba(15,23,42,.82) 75%), url("assets/hero.jpg");
    }
    body[data-tier="premium"] .hero-inner { max-width: 52rem; margin: 0; width: 100%; padding: 0 4vw; }
    body[data-tier="premium"] .hero h1 {
      font-size: clamp(2.6rem, 7vw, 4.4rem); line-height: 1.05; font-weight: 700; max-width: 16ch;
    }
    body[data-tier="premium"] .hero p.lead { font-size: 1.25rem; max-width: 36rem; margin-inline: 0; }
    body[data-tier="premium"] .trust-row,
    body[data-tier="premium"] .hero-ctas { justify-content: flex-start; }
    body[data-tier="premium"] .section { max-width: 1100px; padding: 5rem 1.5rem; }
    body[data-tier="premium"] .section h2 { font-size: 2.1rem; }
    body[data-tier="premium"] .service-card {
      border: 0; border-radius: 18px; padding: 1.6rem; background: #fff;
      box-shadow: 0 18px 48px rgba(15,23,42,0.1);
    }
    body[data-tier="premium"] .service-card:hover {
      transform: translateY(-6px); box-shadow: 0 24px 56px rgba(15,23,42,0.16);
    }
    body[data-tier="premium"] .btn { border-radius: 12px; padding: 1rem 1.75rem; }
"""
