"""Tier design-system CSS for Path A Factory ZIP landings.

R3.1 — Premium Visual System: perception, not polish.
Basic = clean · Business = confident · Premium = another product class.
"""

from __future__ import annotations

from typing import Protocol

# Cinematic Hero layouts reserved for Premium product class (R3.1).
PREMIUM_HERO_POOL = ("B", "D", "F")
BASIC_HERO_PREFER = ("A", "C")


class _Style(Protocol):
    primary: str
    primary_dark: str
    accent: str
    hero_gradient: str


def apply_tier_palette(style: _Style, tier: str) -> tuple[str, str, str, str]:
    """Return (primary, primary_dark, accent, hero_gradient) for the package class.

    Premium keeps niche hue identity and adds champagne as accent — it must not
    repaint Kanzlei / Handwerk / Restaurant into one luxury gray.
    """
    t = tier if tier in ("basic", "business", "premium") else (
        "premium" if tier == "connected" else "business" if tier == "standalone" else "basic"
    )
    p, pd, acc, grad = style.primary, style.primary_dark, style.accent, style.hero_gradient
    if t == "basic":
        return p, pd, acc, grad
    if t == "business":
        return p, pd, acc, f"linear-gradient(160deg,#0f172a 0%,{pd} 55%,{p} 100%)"
    # Premium — niche primary survives; champagne accent + deeper ink hero wash.
    return (
        p,
        pd,
        "#c5a572",
        f"linear-gradient(165deg,#050505 0%,{pd} 42%,{p} 100%)",
    )


def tier_perception_css(tier: str) -> str:
    """Last-word CSS after Hero Composer — must win the 3-second Premium Test."""
    t = tier if tier in ("basic", "business", "premium") else (
        "premium" if tier == "connected" else "business" if tier == "standalone" else "basic"
    )
    if t == "basic":
        return """
    /* R3.1 Basic — finished modern (not flat white paper) */
    body[data-tier="basic"] {
      --surface: #f7f4ef; --line: #e4ebe6;
      background: #f7f4ef;
    }
    body[data-tier="basic"] .hero {
      min-height: min(88vh, 820px);
    }
    body[data-tier="basic"] .section {
      padding-top: 3.5rem; padding-bottom: 3.5rem; max-width: none;
      padding-left: max(1.25rem, calc(50vw - 460px));
      padding-right: max(1.25rem, calc(50vw - 460px));
    }
    body[data-tier="basic"] .section h2 { font-size: 1.65rem; font-weight: 700; letter-spacing: -0.02em; }
    body[data-tier="basic"] .about {
      background: linear-gradient(135deg, color-mix(in srgb, var(--p) 10%, #f7f4ef), #ebe8e1);
    }
    body[data-tier="basic"] .services-block {
      background: color-mix(in srgb, var(--p) 6%, #fff);
    }
    body[data-tier="basic"] #contact {
      background: linear-gradient(160deg, #1c1917, color-mix(in srgb, var(--pd) 70%, #0c0a09));
      color: #fafaf9;
    }
    body[data-tier="basic"] #contact h2,
    body[data-tier="basic"] #contact .muted { color: #fafaf9; }
    body[data-tier="basic"] .service-card {
      border-radius: var(--card-radius, 14px);
      border: 1px solid color-mix(in srgb, var(--p) 18%, #e2e8f0);
      box-shadow: 0 10px 28px rgba(28,25,23,0.06);
      background: rgba(255,255,255,0.72);
    }
    body[data-tier="basic"] .btn { border-radius: var(--btn-radius, 999px); }
"""
    if t == "business":
        return """
    /* R3.1 Business — confident, modern, commercial (niche fonts from Design Engine) */
    body[data-tier="business"] {
      --muted: #475569; --surface: #f8fafc; --line: #cbd5e1;
      background: #f8fafc;
    }
    body[data-tier="business"] .topbar {
      background: rgba(15,23,42,0.97); color: #fff;
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    body[data-tier="business"] .topbar a { color: var(--acc); }
    body[data-tier="business"] .section {
      max-width: none;
      padding: 4.25rem max(1.5rem, calc(50vw - 500px));
    }
    body[data-tier="business"] .section h2 {
      font-size: 1.85rem; font-weight: 800; letter-spacing: -0.03em;
    }
    body[data-tier="business"] .about {
      background: linear-gradient(135deg, #e8eef6 0%, #f1f5f9 55%, #e2e8f0 100%);
    }
    body[data-tier="business"] .benefits {
      background: linear-gradient(180deg, #0f172a, #1e293b); color: #f8fafc;
    }
    body[data-tier="business"] .benefits h2 { color: #f8fafc; }
    body[data-tier="business"] .benefits li { color: rgba(248,250,252,0.88); }
    body[data-tier="business"] .services-block { background: #f1f5f9; }
    body[data-tier="business"] #trust {
      background: linear-gradient(160deg, #1e293b, #0f172a); color: #f8fafc;
    }
    body[data-tier="business"] #trust h2 { color: #f8fafc; }
    body[data-tier="business"] #faq { background: #f8fafc; }
    body[data-tier="business"] #maps { background: #e8eef6; }
    body[data-tier="business"] #contact { background: #ffffff; }
    body[data-tier="business"] .service-card {
      border-left: 3px solid var(--p); border-radius: var(--card-radius, 8px);
      box-shadow: 0 8px 24px rgba(15,23,42,0.07); background: #fff;
    }
    body[data-tier="business"] .btn { border-radius: var(--btn-radius, 8px); font-weight: 800; }
"""

    return """
    /* R3.1 Premium — studio spacing/motion + champagne accents; niche hue survives */
    body[data-tier="premium"] {
      --acc: #c5a572;
      --surface: #f7f3eb; --line: #e7e5e4;
      background: #f7f3eb;
      color: var(--ink);
    }
    body[data-tier="premium"] .topbar {
      background: rgba(12,10,9,0.72); color: #fafaf9;
      backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
      border-bottom: 1px solid rgba(197,165,114,0.22);
    }
    body[data-tier="premium"] .topbar a {
      color: #fafaf9; letter-spacing: 0.04em; font-size: 0.82rem; text-transform: uppercase;
    }
    body[data-tier="premium"] .brand .logo-fallback {
      background: linear-gradient(145deg,var(--p),var(--pd)); color: #fafaf9; border-radius: 999px;
    }
    body[data-tier="premium"] .hero h1,
    body[data-tier="premium"] .section h2,
    body[data-tier="premium"] .mid-cta h2 {
      /* Keep niche display font from Design Engine; only strengthen weight/size */
      font-weight: 600; letter-spacing: -0.03em;
    }
    body[data-tier="premium"][data-hero-layout] .hero.hero-layout-B,
    body[data-tier="premium"][data-hero-layout] .hero.hero-layout-D,
    body[data-tier="premium"][data-hero-layout] .hero.hero-layout-F {
      min-height: 92vh !important;
      padding: 0 !important;
    }
    body[data-tier="premium"][data-hero-layout] .hero.hero-layout-B.has-photo {
      background-image:
        linear-gradient(105deg, rgba(5,5,5,.90) 0%, rgba(28,25,23,.50) 48%, color-mix(in srgb, var(--p) 35%, transparent) 100%),
        url("assets/hero.jpg") !important;
      background-size: cover; background-position: center;
    }
    body[data-tier="premium"][data-hero-layout] .hero.hero-layout-D.has-photo {
      background-image:
        linear-gradient(160deg, rgba(5,5,5,.80), rgba(28,25,23,.42) 45%, color-mix(in srgb, var(--p) 28%, transparent) 100%),
        url("assets/hero.jpg") !important;
    }
    body[data-tier="premium"] .hero-D-panel {
      max-width: 36rem !important;
      padding: 2.5rem 2rem !important;
      border-radius: 2px !important;
      background: rgba(12,10,9,0.72) !important;
      border: 1px solid rgba(197,165,114,0.35) !important;
      backdrop-filter: blur(18px);
      box-shadow: 0 28px 80px rgba(0,0,0,0.45), 0 0 60px rgba(197,165,114,0.12);
    }
    body[data-tier="premium"] .hero-D-panel .btn {
      background: linear-gradient(135deg,#c5a572,#a78b5a) !important;
      color: #0c0a09 !important;
      border: 0 !important;
    }
    body[data-tier="premium"][data-hero-layout] .hero.hero-layout-F {
      background: #050505 !important;
    }
    body[data-tier="premium"] .hero-B-copy h1,
    body[data-tier="premium"] .hero-D-panel h1,
    body[data-tier="premium"] .hero-F-card h1 {
      font-size: clamp(2.8rem, 7.5vw, 4.6rem) !important;
      line-height: 1.02; max-width: 14ch;
      text-shadow: 0 12px 40px rgba(0,0,0,0.35);
    }
    body[data-tier="premium"] .hero p.lead {
      font-size: 1.2rem; max-width: 34rem; color: rgba(250,250,249,0.88);
      font-family: var(--font-body, inherit);
    }
    body[data-tier="premium"] .hero .btn,
    body[data-tier="premium"] .btn {
      background: linear-gradient(135deg,#c5a572,#a78b5a);
      color: #0c0a09; border-radius: 2px; padding: 1.05rem 1.9rem;
      box-shadow: 0 0 0 1px rgba(197,165,114,0.35), 0 18px 40px rgba(0,0,0,0.28);
      letter-spacing: 0.06em; text-transform: uppercase; font-size: 0.82rem;
    }
    body[data-tier="premium"] .hero .btn:hover,
    body[data-tier="premium"] .btn:hover {
      transform: translateY(-3px); filter: brightness(1.06);
    }
    body[data-tier="premium"] .trust-pill {
      border-radius: 2px; border-color: rgba(197,165,114,0.45); color: #fafaf9;
      background: rgba(255,255,255,0.06); letter-spacing: 0.04em;
    }
    body[data-tier="premium"] .hero-B-kpis .hero-kpi strong,
    body[data-tier="premium"] .hero-F-rail .hero-kpi strong {
      color: #c5a572;
    }
    body[data-tier="premium"] .hero-B-band {
      background: linear-gradient(90deg,var(--pd),#c5a572,var(--p));
      height: 3px;
    }
    /* Page rhythm: ink / tint / glass / image — never cream-paper monotony */
    body[data-tier="premium"] .section {
      max-width: none;
      padding: 6.5rem max(1.75rem, calc(50vw - 560px));
    }
    body[data-tier="premium"] .section h2 {
      font-size: clamp(2rem, 3.8vw, 2.75rem); color: var(--ink); margin-bottom: 2rem;
      max-width: 18ch;
    }
    body[data-tier="premium"] .about {
      background:
        linear-gradient(135deg, color-mix(in srgb, var(--p) 12%, #f4f0ea) 0%, #ebe4d8 55%, color-mix(in srgb, var(--pd) 8%, #f7f3eb) 100%);
    }
    body[data-tier="premium"] .benefits {
      background: linear-gradient(180deg, #1c1917 0%, #0c0a09 100%);
      color: #fafaf9;
    }
    body[data-tier="premium"] .benefits h2,
    body[data-tier="premium"] .benefits .why-title { color: #fafaf9; }
    body[data-tier="premium"] .benefits li,
    body[data-tier="premium"] .benefits .muted { color: rgba(250,250,249,0.82); }
    body[data-tier="premium"] .services-block {
      background:
        radial-gradient(ellipse 70% 50% at 90% 0%, color-mix(in srgb, var(--p) 18%, transparent), transparent 55%),
        linear-gradient(180deg, #f3efe7 0%, #e8e2d6 100%);
    }
    body[data-tier="premium"] #trust {
      background: linear-gradient(160deg, color-mix(in srgb, var(--pd) 88%, #0c0a09), #1c1917);
      color: #fafaf9;
    }
    body[data-tier="premium"] #trust h2 { color: #fafaf9; }
    body[data-tier="premium"] #faq {
      background:
        linear-gradient(180deg, rgba(255,255,255,0.55), rgba(255,255,255,0.35)),
        linear-gradient(135deg, color-mix(in srgb, var(--p) 14%, #efe9df), #e4ddd0);
    }
    body[data-tier="premium"] #process {
      background: linear-gradient(180deg, #0c0a09, color-mix(in srgb, var(--pd) 70%, #0c0a09));
      color: #fafaf9;
    }
    body[data-tier="premium"] #process h2 { color: #fafaf9; }
    body[data-tier="premium"] #maps {
      background: linear-gradient(180deg, #ebe4d8, #dfd6c8);
    }
    body[data-tier="premium"] #contact {
      background:
        radial-gradient(circle at 10% 20%, color-mix(in srgb, var(--acc, #c5a572) 22%, transparent), transparent 40%),
        linear-gradient(160deg, #1c1917 0%, #0c0a09 100%);
      color: #fafaf9;
    }
    body[data-tier="premium"] #contact h2,
    body[data-tier="premium"] #contact .muted { color: #fafaf9; }
    body[data-tier="premium"] #contact a { color: #c5a572; }
    body[data-tier="premium"] #calculator {
      background:
        linear-gradient(135deg, color-mix(in srgb, var(--p) 16%, #f0ebe3), #e7e0d4);
      max-width: none;
      padding: 6.5rem max(1.75rem, calc(50vw - 560px));
    }
    body[data-tier="premium"] .showcase {
      background: #0c0a09; color: #fafaf9;
      max-width: none; padding: 6.5rem max(1.75rem, calc(50vw - 560px));
    }
    body[data-tier="premium"] .showcase h2 { color: #fafaf9; }
    body[data-tier="premium"] .showcase .muted { color: #a8a29e; }
    body[data-tier="premium"] .showcase-panel.has-media {
      background-size: cover; background-position: center;
      min-height: 16rem; position: relative; overflow: hidden;
    }
    body[data-tier="premium"] .showcase-single .showcase-full {
      min-height: min(58vh, 640px); border-radius: 2px;
      max-width: none; margin: 0;
    }
    body[data-tier="premium"] .showcase-panel.has-media .cap {
      position: absolute; left: 1rem; bottom: 1rem;
      background: rgba(12,10,9,0.55); backdrop-filter: blur(10px);
      padding: 0.55rem 0.85rem; border-radius: 2px;
      border: 1px solid rgba(197,165,114,0.28);
    }
    body[data-tier="premium"] .service-card,
    body[data-tier="premium"] .svc-card,
    body[data-tier="premium"] .process-card,
    body[data-tier="premium"] .faq-item,
    body[data-tier="premium"] .product-card,
    body[data-tier="premium"] .testimonial-card {
      border: 1px solid rgba(255,255,255,0.35); border-radius: 18px;
      background: rgba(255,255,255,0.55);
      backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
      padding: 2rem 1.65rem;
      box-shadow: 0 24px 60px rgba(28,25,23,0.10), inset 0 1px 0 rgba(255,255,255,0.45);
      transition: transform 0.35s cubic-bezier(0.16,1,0.3,1), box-shadow 0.35s ease;
    }
    body[data-tier="premium"] .svc-glass {
      background: rgba(255,255,255,0.42) !important;
      border: 1px solid rgba(197,165,114,0.28) !important;
    }
    body[data-tier="premium"] .service-card:hover,
    body[data-tier="premium"] .process-card:hover {
      transform: translateY(-8px);
      box-shadow: 0 32px 72px rgba(28,25,23,0.14), 0 0 0 1px rgba(197,165,114,0.25);
    }
    body[data-tier="premium"] .service-card h3,
    body[data-tier="premium"] .faq-item h3 { color: var(--ink); font-family: var(--font-display, Georgia, serif); }
    body[data-tier="premium"] .mid-cta {
      background: linear-gradient(135deg,var(--pd),#1c1917 55%,var(--p));
      box-shadow: inset 0 1px 0 rgba(197,165,114,0.25);
      padding: 5.5rem 1.5rem;
    }
    body[data-tier="premium"] .mid-cta h2 {
      color: #fafaf9; font-size: clamp(2rem, 4vw, 2.8rem);
    }
    body[data-tier="premium"] .premium-signature {
      position: relative; isolation: isolate;
      min-height: min(72vh, 780px); display: grid; place-items: center;
      padding: 5rem 1.5rem; text-align: center; color: #fafaf9;
      background:
        linear-gradient(180deg, rgba(5,5,5,.42), rgba(12,10,9,.82)),
        url("assets/hero.jpg") center/cover no-repeat;
      background-attachment: fixed;
    }
    body[data-tier="premium"] .premium-signature::after {
      content: "";
      position: absolute; inset: auto 12% 18% 12%; height: 1px;
      background: linear-gradient(90deg, transparent, rgba(197,165,114,0.55), transparent);
      pointer-events: none;
    }
    body[data-tier="premium"][data-niche="psychology"] {
      --acc: #c9b8a6;
      background: #f4f1eb;
    }
    body[data-tier="premium"][data-niche="psychology"] .about {
      background:
        linear-gradient(145deg, #e8efe9 0%, #f4f0ea 45%, #dfe8e2 100%);
    }
    body[data-tier="premium"][data-niche="psychology"] .services-block {
      background:
        radial-gradient(ellipse 60% 45% at 0% 100%, rgba(91,124,110,0.18), transparent 55%),
        linear-gradient(180deg, #f7f4ef, #e8efe9);
    }
    body[data-tier="premium"][data-niche="psychology"] .hero-D-panel,
    body[data-tier="premium"][data-niche="psychology"] .hero-B-copy {
      border-color: rgba(201,184,166,0.4) !important;
    }
    body[data-tier="premium"] .premium-signature-copy {
      position: relative; z-index: 1; max-width: 40rem;
    }
    body[data-tier="premium"] .premium-signature-eyebrow {
      letter-spacing: 0.22em; text-transform: uppercase; font-size: 0.72rem;
      color: #c5a572; margin-bottom: 1.25rem;
    }
    body[data-tier="premium"] .premium-signature h2 {
      font-family: var(--font-display, Georgia, "Iowan Old Style", Palatino, serif);
      font-size: clamp(2.2rem, 5vw, 3.4rem); line-height: 1.1;
      font-weight: 600; margin-bottom: 1rem; color: #fafaf9;
      max-width: none;
    }
    body[data-tier="premium"] .premium-signature p {
      color: rgba(250,250,249,0.82); font-size: 1.15rem; margin-bottom: 2rem;
    }
    body[data-tier="premium"] .client-gallery {
      background: #0c0a09; color: #fafaf9; max-width: none;
      padding: 7rem max(1.75rem, calc(50vw - 560px));
    }
    body[data-tier="premium"] .client-gallery h2 { color: #fafaf9; }
    body[data-tier="premium"] .client-gallery .muted { color: #a8a29e; }
    body[data-tier="premium"] .client-photo {
      border-radius: 2px; aspect-ratio: 3/4; box-shadow: 0 20px 50px rgba(0,0,0,0.35);
    }
    body[data-tier="premium"] .client-photo img {
      transition: transform 0.7s cubic-bezier(0.16,1,0.3,1);
    }
    body[data-tier="premium"] .client-photo:hover img { transform: scale(1.06); }
    body[data-tier="premium"] .showcase-panel {
      border-radius: 2px; box-shadow: 0 28px 64px rgba(0,0,0,0.28);
    }
    body[data-tier="premium"] .info-bar,
    body[data-tier="premium"] .trust-strip,
    body[data-tier="premium"] footer {
      background: #0c0a09; color: #d6d3d1;
      border-top: 1px solid rgba(197,165,114,0.2);
    }
    body[data-tier="premium"] .info-bar strong { color: #c5a572; }
    body[data-tier="premium"] .stats {
      background: linear-gradient(180deg,#0c0a09,#1c1917);
      border-top: 1px solid rgba(197,165,114,0.2);
    }
    body[data-tier="premium"] .stat strong { color: #c5a572; font-family: var(--font-display, Georgia, serif); }
    body[data-tier="premium"] .reveal {
      transform: translateY(28px) scale(0.985);
      transition: opacity 0.7s cubic-bezier(0.16,1,0.3,1), transform 0.7s cubic-bezier(0.16,1,0.3,1);
    }
    body[data-tier="premium"] .reveal.active {
      opacity: 1; transform: none;
    }
"""


def tier_stylesheet(tier: str, style: _Style) -> str:
    """Return CSS differentiated by package tier (basic / business / premium)."""
    t = tier if tier in ("basic", "business", "premium") else (
        "premium" if tier == "connected" else "business" if tier == "standalone" else "basic"
    )
    p, pd, acc, grad = apply_tier_palette(style, t)

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
      background-image: linear-gradient(120deg, rgba(15,23,42,.82), rgba(15,23,42,.55)), url("assets/hero.jpg");
      background-size: cover; background-position: center;
    }}
    body[data-niche="psychology"] .hero.has-photo,
    body[data-niche="family_psychology"] .hero.has-photo,
    body[data-niche="dental"] .hero.has-photo {{
      background-image: linear-gradient(105deg, rgba(248,250,252,.55), rgba(15,23,42,.35)), url("assets/hero.jpg");
    }}
    body[data-niche="car_dealership"] .hero.has-photo,
    body[data-niche="restaurant"] .hero.has-photo,
    body[data-niche="handwerk"] .hero.has-photo {{
      background-image: linear-gradient(115deg, rgba(8,10,14,.88), rgba(8,10,14,.5)), url("assets/hero.jpg");
    }}
    .hero .btn {{
      background: var(--acc); color: #0f172a; font-weight: 800;
      box-shadow: 0 8px 28px rgba(0,0,0,.35);
    }}
    body[data-niche="psychology"] .hero .btn,
    body[data-niche="family_psychology"] .hero .btn,
    body[data-niche="dental"] .hero .btn {{
      color: #fff; background: #0f766e;
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
    body[data-tier="basic"] .topbar {
      background: rgba(255,255,255,0.92); color: var(--ink); backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--line);
    }
    body[data-tier="basic"] .topbar a { color: var(--pd); }
"""

    if t == "business":
        return base + """
    body[data-tier="business"] .topbar { background: rgba(15,23,42,0.96); color: #fff; }
    body[data-tier="business"] .topbar a { color: var(--acc); }
"""

    return base + """
    body[data-tier="premium"] .topbar {
      background: rgba(12,10,9,0.55); color: #fff; backdrop-filter: blur(14px);
      border-bottom: 1px solid rgba(197,165,114,0.15);
    }
"""
