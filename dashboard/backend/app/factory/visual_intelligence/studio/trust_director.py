"""Trust Director — certificates, guarantees, reviews, map, contacts."""

from __future__ import annotations

import re
from typing import Any

ENGINE_ID = "trust_director_v1"

TRUST_NICHES = frozenset(
    {"dental", "law", "auto", "handwerk", "medical", "clinic", "construction", "bau"}
)


def decide_trust(*, package_id: str, niche: str | None = None) -> dict[str, Any]:
    pid = (package_id or "basic").strip().lower()
    niche_key = (niche or "generic").strip().lower()
    heavy = niche_key in TRUST_NICHES

    if heavy:
        choice = "High-trust vertical pack"
        reason = (
            "Для стоматологий / юристов / авто / стройки доверие важнее декора: "
            "сертификаты, гарантии, отзывы, карта и контакты на видных местах."
        )
        apply = {
            "certs_near_hero": True,
            "guarantees_in_benefits": True,
            "reviews_before_contact": True,
            "map_with_contacts": True,
            "brands_strip": pid != "basic",
            "trust_density": "high",
        }
    elif pid == "premium":
        choice = "Premium trust layer"
        reason = "Premium: отзывы и доказательства рядом с CTA."
        apply = {
            "certs_near_hero": False,
            "guarantees_in_benefits": True,
            "reviews_before_contact": True,
            "map_with_contacts": True,
            "brands_strip": True,
            "trust_density": "rich",
        }
    else:
        choice = "Clean trust basics"
        reason = "Базовые контакты и доверие без перегруза."
        apply = {
            "certs_near_hero": False,
            "guarantees_in_benefits": False,
            "reviews_before_contact": False,
            "map_with_contacts": True,
            "brands_strip": False,
            "trust_density": "light",
        }

    return {
        "engine": ENGINE_ID,
        "role": "Trust Director",
        "choice": choice,
        "reason_ru": reason,
        "reason_en": reason,
        "apply": apply,
    }


def trust_director_css(decision: dict[str, Any]) -> str:
    density = str((decision.get("apply") or {}).get("trust_density") or "light")
    return f"""
/* Trust Director — density={density} */
body[data-trust-density="{density}"] #trust,
body[data-trust-density="{density}"] .trust {{
  scroll-margin-top: 4rem;
}}
body[data-trust-density="high"] .hero-certs,
body[data-trust-density="high"] .trust-badges {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 0.75rem;
  margin-top: 1rem;
}}
body[data-trust-density="high"] .hero-certs span,
body[data-trust-density="high"] .trust-badges span {{
  font-size: 0.78rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 0.35rem 0.65rem;
  border: 1px solid rgba(15,23,42,0.12);
  border-radius: 999px;
  background: rgba(255,255,255,0.72);
}}
body[data-trust-density="high"] #maps,
body[data-trust-density="high"] #contact {{
  background: #f8fafc;
}}
"""


def apply_trust_html(html: str, decision: dict[str, Any]) -> str:
    apply = decision.get("apply") or {}
    density = str(apply.get("trust_density") or "light")
    attrs = [f'data-trust-density="{density}"']
    if apply.get("certs_near_hero"):
        attrs.append('data-trust-certs="hero"')
    if apply.get("map_with_contacts"):
        attrs.append('data-trust-map="1"')

    def _body(m):
        tag = m.group(0)
        extra = " ".join(a for a in attrs if a.split("=")[0] not in tag)
        if not extra:
            return tag
        return tag[:-1] + " " + extra + ">"

    out = re.sub(r"<body\b[^>]*>", _body, html, count=1, flags=re.I)

    # Inject cert chips into hero if required and missing
    if apply.get("certs_near_hero") and "hero-certs" not in out.lower():
        chips = (
            '<div class="hero-certs trust-badges" data-trust-director="certs">'
            "<span>Zertifiziert</span><span>Garantie</span><span>Bewertungen</span>"
            "</div>"
        )
        out2, n = re.subn(
            r'(<(?:header|section|div)\b[^>]*\bclass=["\'][^"\']*\bhero\b[^"\']*["\'][^>]*>)(.*?)(</(?:header|section|div)>)',
            lambda m: m.group(1) + m.group(2) + chips + m.group(3),
            out,
            count=1,
            flags=re.I | re.S,
        )
        if n:
            out = out2
    return out
