"""Landing Page HTML builder — sandbox only, no external APIs."""

from __future__ import annotations

import re

from dataclasses import dataclass

from app.factory.analyzer import AnalysisResult


@dataclass
class BuildStyle:
    primary: str
    primary_dark: str
    accent: str
    hero_gradient: str


_STYLES = {
    "dental": BuildStyle("#0ea5e9", "#0369a1", "#22d3ee", "linear-gradient(135deg,#0c4a6e,#0ea5e9)"),
    "auto": BuildStyle("#f97316", "#c2410c", "#fbbf24", "linear-gradient(135deg,#1c1917,#ea580c)"),
    "law": BuildStyle("#1e3a5f", "#0f172a", "#c9a227", "linear-gradient(135deg,#0f172a,#1e40af)"),
    "beauty": BuildStyle("#a855f7", "#7e22ce", "#f472b6", "linear-gradient(135deg,#581c87,#c026d3)"),
    "energy": BuildStyle("#16a34a", "#15803d", "#facc15", "linear-gradient(135deg,#14532d,#16a34a)"),
    "green": BuildStyle("#22c55e", "#166534", "#86efac", "linear-gradient(135deg,#14532d,#22c55e)"),
    "generic": BuildStyle("#6366f1", "#4338ca", "#818cf8", "linear-gradient(135deg,#312e81,#6366f1)"),
}

_FORBIDDEN_SNIPPETS = (
    "уточним после",
    "Landing Page —",
    "Понятное предложение на главном экране",
    "Готовность к публикации после вашего одобрения",
)


def build_landing_html(
    analysis: AnalysisResult,
    *,
    modern: bool = False,
    blue_boost: bool = False,
    calculator: bool = False,
    include_testimonials: bool = False,
    large_headline: bool = False,
) -> str:
    style = _STYLES.get(analysis.niche, _STYLES["generic"])
    if blue_boost or analysis.niche == "dental":
        style = _STYLES["dental"]
    if modern:
        style = BuildStyle(style.primary, style.primary_dark, style.accent, f"linear-gradient(160deg,#0f172a,{style.primary})")

    descriptions = analysis.service_descriptions
    if len(descriptions) < len(analysis.services):
        descriptions = descriptions + ("",) * (len(analysis.services) - len(descriptions))

    services_html = "".join(
        f'<li class="service-card"><h3>{title}</h3><p class="service-desc">{desc}</p></li>'
        for title, desc in zip(analysis.services, descriptions)
    )
    trust_html = "".join(f'<span class="trust-pill">{t}</span>' for t in analysis.trust_points)
    benefits_html = "".join(f"<li>{b}</li>" for b in analysis.benefits)
    h1_class = ' class="large"' if large_headline else ""
    page_title = f"{analysis.business_name} — {analysis.subtitle[:60]}"
    calc_block = ""
    if calculator:
        calc_block = """
    <section class="section calculator" id="calculator">
      <h2>Kostenrechner</h2>
      <p class="muted">Unverbindliche Schätzung — Details klären wir im Gespräch.</p>
      <div class="calc-grid">
        <label>Leistung<select id="svc"><option>Basis</option><option>Standard</option><option>Premium</option></select></label>
        <label>Anzahl<input type="number" id="qty" value="1" min="1" max="10"></label>
        <p class="calc-result">Summe: <strong id="total">ab 49 €</strong></p>
      </div>
    </section>
    <script>
      (function(){
        const prices = {0:49,1:99,2:199};
        function upd(){
          const s = document.getElementById('svc').selectedIndex;
          const q = Math.max(1, parseInt(document.getElementById('qty').value||'1',10));
          document.getElementById('total').textContent = 'ab ' + (prices[s]*q) + ' €';
        }
        document.getElementById('svc').onchange = upd;
        document.getElementById('qty').oninput = upd;
      })();
    </script>
"""

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{page_title}</title>
  <meta name="description" content="{analysis.subtitle[:160]}">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; color: #0f172a; line-height: 1.65; }}
    .topbar {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 0.75rem 1.5rem; background: rgba(15,23,42,0.92); color: #fff;
      position: sticky; top: 0; z-index: 10;
    }}
    .topbar strong {{ font-size: 1rem; letter-spacing: -0.01em; }}
    .topbar a {{ color: {style.accent}; text-decoration: none; font-weight: 600; font-size: 0.9rem; }}
    .hero {{
      background: {style.hero_gradient};
      color: #fff;
      padding: 4rem 1.5rem 5rem;
      text-align: center;
    }}
    .hero h1 {{ font-size: clamp(1.85rem, 4.5vw, 3rem); font-weight: 800; letter-spacing: -0.02em; margin-bottom: 1rem; max-width: 44rem; margin-inline: auto; }}
    .hero h1.large {{ font-size: clamp(2.25rem, 5vw, 3.5rem); }}
    .hero p {{ font-size: 1.15rem; opacity: 0.95; max-width: 38rem; margin: 0 auto 1.5rem; }}
    .trust-row {{ display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center; margin-bottom: 2rem; }}
    .trust-pill {{ background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.25); padding: 0.35rem 0.85rem; border-radius: 999px; font-size: 0.8rem; }}
    .btn {{
      display: inline-block;
      background: {style.accent};
      color: #0f172a;
      font-weight: 700;
      padding: 0.875rem 2rem;
      border-radius: 999px;
      text-decoration: none;
      box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }}
    .section {{ padding: 3.5rem 1.5rem; max-width: 960px; margin: 0 auto; }}
    .section h2 {{ font-size: 1.75rem; margin-bottom: 1.25rem; color: {style.primary_dark}; }}
    .services {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); list-style: none; }}
    .service-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1.25rem;
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    .service-card h3 {{ font-size: 1.05rem; margin-bottom: 0.5rem; color: {style.primary_dark}; }}
    .service-desc {{ font-size: 0.92rem; color: #475569; line-height: 1.5; }}
    .service-card:hover {{ transform: translateY(-2px); box-shadow: 0 12px 24px rgba(0,0,0,0.08); }}
    .about {{ background: #f1f5f9; }}
    .benefits {{ background: #fff; }}
    .benefits ul {{ list-style: none; display: grid; gap: 0.75rem; }}
    .benefits li {{ padding-left: 1.5rem; position: relative; }}
    .benefits li::before {{ content: "✓"; position: absolute; left: 0; color: {style.primary}; font-weight: 700; }}
    .muted {{ color: #64748b; margin-bottom: 1rem; }}
    .contact-grid {{ display: grid; gap: 0.5rem; font-size: 1rem; }}
    .calculator {{ background: #fff; border-top: 1px solid #e2e8f0; }}
    .calc-grid {{ display: grid; gap: 1rem; max-width: 400px; }}
    .calc-grid label {{ display: flex; flex-direction: column; gap: 0.5rem; font-weight: 600; }}
    .calc-grid select, .calc-grid input {{ padding: 0.5rem; border-radius: 8px; border: 1px solid #cbd5e1; }}
    .calc-result {{ font-size: 1.25rem; margin-top: 0.5rem; }}
    .testimonials {{ background: #f8fafc; }}
    .testimonial-grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
    .testimonial-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.25rem; }}
    .testimonial-card cite {{ display: block; margin-top: 0.75rem; font-size: 0.875rem; color: #64748b; }}
    footer {{ text-align: center; padding: 2rem; color: #94a3b8; font-size: 0.875rem; background: #0f172a; color: #cbd5e1; }}
    @media (max-width: 640px) {{
      .hero {{ padding: 3rem 1rem 4rem; }}
      .section {{ padding: 2.5rem 1rem; }}
    }}
  </style>
</head>
<body>
  <nav class="topbar">
    <strong>{analysis.business_name}</strong>
    <a href="#contact">{analysis.cta_label}</a>
  </nav>
  <header class="hero">
    <h1{h1_class}>{analysis.headline}</h1>
    <p>{analysis.subtitle}</p>
    <div class="trust-row">{trust_html}</div>
    <a class="btn" href="#contact">{analysis.cta_label}</a>
  </header>
  <section class="section" id="services">
    <h2>Leistungen</h2>
    <ul class="services">{services_html}</ul>
  </section>
  <section class="section benefits">
    <h2>Warum {analysis.business_name}</h2>
    <ul>{benefits_html}</ul>
  </section>
  <section class="section about">
    <h2>Über uns</h2>
    <p>{analysis.about_text}</p>
  </section>
  {calc_block}
  {_testimonials_section(include_testimonials)}
  <section class="section" id="contact">
    <h2>Kontakt</h2>
    <p class="muted">Schreiben oder rufen Sie an — wir melden uns schnellstmöglich.</p>
    <div class="contact-grid">
      <p><strong>Telefon:</strong> <a href="tel:{_tel_href(analysis.phone)}">{analysis.phone}</a></p>
      <p><strong>E-Mail:</strong> <a href="mailto:{analysis.email}">{analysis.email}</a></p>
      <p><strong>Öffnungszeiten:</strong> {analysis.hours}</p>
    </div>
  </section>
  <footer>{analysis.business_name} · © {analysis.business_name}</footer>
</body>
</html>
"""
    lower = html.lower()
    for snippet in _FORBIDDEN_SNIPPETS:
        if snippet.lower() in lower:
            raise ValueError(f"forbidden_copy_snippet:{snippet}")
    return html


def _tel_href(phone: str) -> str:
    return re.sub(r"[^\d+]", "", phone)


def _testimonials_section(enabled: bool) -> str:
    if not enabled:
        return ""
    return """
  <section class="section testimonials" id="testimonials">
    <h2>Kundenstimmen</h2>
    <div class="testimonial-grid">
      <blockquote class="testimonial-card"><p>«Professionell und zuverlässig — klare Empfehlung.»</p><cite>— Anna K.</cite></blockquote>
      <blockquote class="testimonial-card"><p>«Transparente Preise und gutes Ergebnis.»</p><cite>— Michael W.</cite></blockquote>
    </div>
  </section>
"""
