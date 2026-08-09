"""Conversion Director — site must sell, not only look good."""

from __future__ import annotations

import re
from typing import Any

ENGINE_ID = "conversion_director_v1"


def _clip(n: float) -> int:
    return max(0, min(100, int(round(n))))


def decide_conversion(*, package_id: str, niche: str | None = None) -> dict[str, Any]:
    pid = (package_id or "basic").strip().lower()
    niche_key = (niche or "").strip().lower()
    # Trust-heavy niches need mid CTA + contact early
    mid_cta = pid != "basic" or niche_key in ("dental", "law", "auto", "handwerk")
    return {
        "engine": ENGINE_ID,
        "role": "Conversion Director",
        "choice": "Sell-first layout",
        "reason_ru": "Кнопки, форма и доверие расставлены ради конверсии, не декора.",
        "reason_en": "CTA, form and trust placed for conversion, not decoration.",
        "apply": {
            "require_mid_cta": mid_cta,
            "cta_after_services": True,
            "contact_above_fold_hint": pid != "basic",
            "faq_before_footer": True,
        },
    }


def score_conversion_html(html: str) -> dict[str, Any]:
    low = html.lower()
    has_hero = bool(re.search(r'\bclass=["\'][^"\']*\bhero\b', html, re.I))
    ctas = len(re.findall(r'href=["\']#contact["\']|class=["\'][^"\']*\bbtn\b', html, re.I))
    has_mid = "mid-cta" in low or 'id="mid-cta"' in low or "data-conversion-mid-cta" in low
    has_form = "<form" in low
    has_trust = any(x in low for x in ("trust", "testimonial", "review", "#trust"))
    has_contact = 'id="contact"' in low or "href=\"#contact\"" in low
    has_wa = "whatsapp" in low or "wa.me" in low
    has_faq = 'id="faq"' in low or "faq" in low

    hero = 92 if has_hero else 40
    cta = _clip(55 + min(40, ctas * 8) + (12 if has_mid else 0))
    trust = 91 if has_trust else 62
    contact = _clip(70 + (15 if has_contact else 0) + (13 if has_form or has_wa else 0))
    booking = _clip(60 + (20 if has_form else 0) + (8 if has_wa else 0) + (10 if has_faq else 0))

    recs: list[str] = []
    if not has_mid and cta < 95:
        recs.append("Добавить второй CTA после блока услуг.")
    if contact < 90:
        recs.append("Усилить видимость контактов / формы.")
    if trust < 85:
        recs.append("Поднять блок доверия / отзывов выше.")
    if not recs:
        recs.append("Hold — conversion structure OK.")

    overall = _clip(hero * 0.2 + cta * 0.3 + trust * 0.2 + contact * 0.2 + booking * 0.1)
    return {
        "engine": ENGINE_ID,
        "scores": {
            "hero": hero,
            "cta": cta,
            "trust": trust,
            "contact_visibility": contact,
            "booking_flow": booking,
        },
        "overall": overall,
        "hero_status": "PASS" if hero >= 80 else "FAIL",
        "recommendations": recs,
        "markers": {
            "has_mid_cta": has_mid,
            "has_form": has_form,
            "has_contact": has_contact,
        },
    }


def conversion_director_css() -> str:
    return """
/* Conversion Director */
.conversion-mid-cta,
[data-conversion-mid-cta="1"] {
  text-align: center;
  padding: 2.75rem 1.25rem;
  margin: 0;
  background: linear-gradient(180deg, rgba(15,23,42,0.04), rgba(15,23,42,0.02));
}
.conversion-mid-cta .btn { font-weight: 600; }
body[data-conversion="1"] .topbar-cta { box-shadow: 0 6px 18px rgba(15,23,42,0.12); }
"""


def apply_conversion_html(html: str, decision: dict[str, Any] | None = None) -> str:
    """Inject second CTA after services when Conversion Director requires it."""
    apply = (decision or {}).get("apply") or {}
    if not apply.get("require_mid_cta") and not apply.get("cta_after_services"):
        return html
    low = html.lower()
    if "mid-cta" in low or "data-conversion-mid-cta" in low:
        return html

    # Find CTA label from existing primary button if possible
    m = re.search(
        r'<a\b[^>]*href=["\']#contact["\'][^>]*>(.*?)</a>',
        html,
        re.I | re.S,
    )
    label = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else "Kontakt"
    if not label:
        label = "Kontakt"

    block = f"""
<section class="section conversion-mid-cta mid-cta" id="mid-cta" data-conversion-mid-cta="1">
  <h2>{label}</h2>
  <p class="muted">Jetzt unverbindlich anfragen.</p>
  <a class="btn" href="#contact">{label}</a>
</section>
"""
    # Prefer insert after services section
    for pattern in (
        r'(</section>\s*)(?=<section\b[^>]*\bid=["\'](?:faq|trust|contact|maps))',
        r'(</section>\s*)(?=<section\b[^>]*\bclass=["\'][^"\']*\b(?:faq|trust|contact))',
    ):
        out, n = re.subn(pattern, r"\1" + block, html, count=1, flags=re.I)
        if n:
            html = out
            break
    else:
        html = re.sub(r"</main>", block + "</main>", html, count=1, flags=re.I) if "</main>" in low else (
            re.sub(r"</body>", block + "</body>", html, count=1, flags=re.I)
        )

    html = re.sub(
        r"<body\b([^>]*)>",
        lambda m: (
            m.group(0)
            if "data-conversion=" in m.group(0)
            else m.group(0)[:-1] + ' data-conversion="1">'
        ),
        html,
        count=1,
        flags=re.I,
    )
    return html
