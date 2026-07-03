"""Surgical HTML patches for Improve — avoid full rebuild when possible."""

from __future__ import annotations

import re

_TESTIMONIALS_BLOCK = """
  <section class="section testimonials" id="testimonials">
    <h2>Отзывы клиентов</h2>
    <div class="testimonial-grid">
      <blockquote class="testimonial-card">
        <p>«Профессионально, быстро и без лишней суеты. Рекомендую.»</p>
        <cite>— Анна К.</cite>
      </blockquote>
      <blockquote class="testimonial-card">
        <p>«Понятные цены и внимательное отношение. Вернусь снова.»</p>
        <cite>— Михаил В.</cite>
      </blockquote>
      <blockquote class="testimonial-card">
        <p>«Отличный сервис — именно то, что искал.»</p>
        <cite>— Елена С.</cite>
      </blockquote>
    </div>
  </section>
"""

_TESTIMONIALS_CSS = """
    .testimonials { background: #f8fafc; }
    .testimonial-grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
    .testimonial-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.25rem; font-style: normal; }
    .testimonial-card cite { display: block; margin-top: 0.75rem; font-size: 0.875rem; color: #64748b; font-style: normal; }
"""


def try_patch(html: str, feedback: str) -> tuple[str, list[str]]:
    """Apply targeted edits. Returns (html, list of applied patch names)."""
    lower = feedback.lower()
    applied: list[str] = []
    out = html

    if any(w in lower for w in ("отзыв", "review", "testimonial", "клиент говор")):
        if 'id="testimonials"' not in out:
            out = _inject_testimonials(out)
            applied.append("testimonials")

    if any(w in lower for w in ("крупн", "больше заголов", "headline", "заголовок")):
        out = _enlarge_headline(out)
        applied.append("larger_headline")

    if any(w in lower for w in ("строг", "строже", "минимал", "профессион")):
        out = _add_body_class(out, "theme-strict")
        applied.append("strict_theme")

    return out, applied


def _inject_testimonials(html: str) -> str:
    if _TESTIMONIALS_CSS.strip() not in html:
        html = html.replace("</style>", _TESTIMONIALS_CSS + "\n  </style>", 1)
    marker = '<section class="section" id="contact">'
    if marker in html:
        return html.replace(marker, _TESTIMONIALS_BLOCK + "\n  " + marker, 1)
    return html.replace("</body>", _TESTIMONIALS_BLOCK + "\n</body>", 1)


def _enlarge_headline(html: str) -> str:
    if ".hero h1.large" not in html:
        html = html.replace(
            ".hero h1 {",
            ".hero h1.large { font-size: clamp(2.75rem, 6vw, 4rem) !important; }\n    .hero h1 {",
            1,
        )
    return re.sub(r"(<header class=\"hero\">\s*<h1)(>)", r'\1 class="large"\2', html, count=1)


def _add_body_class(html: str, class_name: str) -> str:
    if f'class="{class_name}"' in html:
        return html
    return html.replace("<body>", f'<body class="{class_name}">', 1)
