"""Landing Page HTML builder — sandbox only, no external APIs."""

from __future__ import annotations

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
    "beauty": BuildStyle("#a855f7", "#7e22ce", "#f472b6", "linear-gradient(135deg,#581c87,#c026d3)"),
    "generic": BuildStyle("#6366f1", "#4338ca", "#818cf8", "linear-gradient(135deg,#312e81,#6366f1)"),
}


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

    services_html = "".join(f'<li class="service-card"><h3>{s}</h3></li>' for s in analysis.services)
    trust_html = "".join(f'<span class="trust-pill">{t}</span>' for t in analysis.trust_points)
    h1_class = ' class="large"' if large_headline else ""
    calc_block = ""
    if calculator:
        calc_block = """
    <section class="section calculator" id="calculator">
      <h2>Калькулятор стоимости</h2>
      <p class="muted">Оценка предварительная — уточните детали у менеджера.</p>
      <div class="calc-grid">
        <label>Услуга<select id="svc"><option>Базовая</option><option>Стандарт</option><option>Премиум</option></select></label>
        <label>Количество<input type="number" id="qty" value="1" min="1" max="10"></label>
        <p class="calc-result">Итого: <strong id="total">от 49 €</strong></p>
      </div>
    </section>
    <script>
      (function(){
        const prices = {0:49,1:99,2:199};
        function upd(){
          const s = document.getElementById('svc').selectedIndex;
          const q = Math.max(1, parseInt(document.getElementById('qty').value||'1',10));
          document.getElementById('total').textContent = 'от ' + (prices[s]*q) + ' €';
        }
        document.getElementById('svc').onchange = upd;
        document.getElementById('qty').oninput = upd;
      })();
    </script>
"""

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{analysis.business_name} — Landing Page</title>
  <meta name="description" content="{analysis.subtitle[:160]}">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; color: #0f172a; line-height: 1.65; }}
    .hero {{
      background: {style.hero_gradient};
      color: #fff;
      padding: 4.5rem 1.5rem 5.5rem;
      text-align: center;
    }}
    .hero h1 {{ font-size: clamp(2.25rem, 5vw, 3.25rem); font-weight: 800; letter-spacing: -0.02em; margin-bottom: 1rem; }}
    .hero h1.large {{ font-size: clamp(2.75rem, 6vw, 4rem); }}
    .hero p {{ font-size: 1.2rem; opacity: 0.95; max-width: 38rem; margin: 0 auto 1.5rem; }}
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
    .section h2 {{ font-size: 1.75rem; margin-bottom: 1.5rem; color: {style.primary_dark}; }}
    .services {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); list-style: none; }}
    .service-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1.25rem;
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    .service-card:hover {{ transform: translateY(-2px); box-shadow: 0 12px 24px rgba(0,0,0,0.08); }}
    .about {{ background: #f1f5f9; }}
    .muted {{ color: #64748b; margin-bottom: 1rem; }}
    .calculator {{ background: #fff; border-top: 1px solid #e2e8f0; }}
    .calc-grid {{ display: grid; gap: 1rem; max-width: 400px; }}
    .calc-grid label {{ display: flex; flex-direction: column; gap: 0.5rem; font-weight: 600; }}
    .calc-grid select, .calc-grid input {{ padding: 0.5rem; border-radius: 8px; border: 1px solid #cbd5e1; }}
    .calc-result {{ font-size: 1.25rem; margin-top: 0.5rem; }}
    .testimonials {{ background: #f8fafc; }}
    .testimonial-grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
    .testimonial-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.25rem; }}
    .testimonial-card cite {{ display: block; margin-top: 0.75rem; font-size: 0.875rem; color: #64748b; }}
    footer {{ text-align: center; padding: 2rem; color: #94a3b8; font-size: 0.875rem; }}
    @media (max-width: 640px) {{
      .hero {{ padding: 3rem 1rem 4rem; }}
      .section {{ padding: 2.5rem 1rem; }}
    }}
  </style>
</head>
<body>
  <header class="hero">
    <h1{h1_class}>{analysis.headline}</h1>
    <p>{analysis.subtitle}</p>
    <div class="trust-row">{trust_html}</div>
    <a class="btn" href="#contact">{analysis.cta_label}</a>
  </header>
  <section class="section">
    <h2>Наши услуги</h2>
    <ul class="services">{services_html}</ul>
  </section>
  <section class="section about">
    <h2>О нас</h2>
    <p>{analysis.business_name} — команда профессионалов, которая ценит качество, прозрачность и комфорт каждого клиента.</p>
  </section>
  {calc_block}
  {_testimonials_section(include_testimonials)}
  <section class="section" id="contact">
    <h2>Контакты</h2>
    <p class="muted">Оставьте заявку — мы свяжемся с вами в рабочее время.</p>
    <p><strong>Телефон:</strong> +7 (000) 000-00-00<br><strong>Email:</strong> hello@example.com</p>
  </section>
  <footer>{analysis.business_name} · все права защищены</footer>
</body>
</html>
"""


def _testimonials_section(enabled: bool) -> str:
    if not enabled:
        return ""
    return """
  <section class="section testimonials" id="testimonials">
    <h2>Отзывы клиентов</h2>
    <div class="testimonial-grid">
      <blockquote class="testimonial-card"><p>«Профессионально и внимательно. Рекомендую.»</p><cite>— Анна К.</cite></blockquote>
      <blockquote class="testimonial-card"><p>«Понятные цены, отличный результат.»</p><cite>— Михаил В.</cite></blockquote>
    </div>
  </section>
"""
