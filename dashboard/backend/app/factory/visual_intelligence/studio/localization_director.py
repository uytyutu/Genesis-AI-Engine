"""Localization Director — market-specific experience (DE/FR/ES/US…)."""

from __future__ import annotations

from typing import Any

ENGINE_ID = "localization_director_v1"

MARKET_PACKS: dict[str, dict[str, Any]] = {
    "DE": {
        "label": "Germany · DACH",
        "reason_ru": "Impressum, Datenschutz, строгий стиль.",
        "legal": ["impressum", "datenschutz"],
        "style": "strict",
        "social_proof_weight": "medium",
        "portfolio_weight": "medium",
        "cta_tone": "formal",
    },
    "AT": {
        "label": "Austria · DACH",
        "reason_ru": "Impressum / Datenschutz, строгий DACH-стиль.",
        "legal": ["impressum", "datenschutz"],
        "style": "strict",
        "social_proof_weight": "medium",
        "portfolio_weight": "medium",
        "cta_tone": "formal",
    },
    "CH": {
        "label": "Switzerland · DACH",
        "reason_ru": "Юридическая ясность и сдержанный тон.",
        "legal": ["impressum", "datenschutz"],
        "style": "strict",
        "social_proof_weight": "medium",
        "portfolio_weight": "medium",
        "cta_tone": "formal",
    },
    "FR": {
        "label": "France",
        "reason_ru": "Больше портфолио и визуальных кейсов.",
        "legal": ["mentions_legales"],
        "style": "editorial",
        "social_proof_weight": "medium",
        "portfolio_weight": "high",
        "cta_tone": "elegant",
    },
    "ES": {
        "label": "Spain",
        "reason_ru": "Больше социальных доказательств и отзывов.",
        "legal": ["aviso_legal"],
        "style": "warm",
        "social_proof_weight": "high",
        "portfolio_weight": "medium",
        "cta_tone": "friendly",
    },
    "US": {
        "label": "United States",
        "reason_ru": "Прямой CTA и иной паттерн доверия (reviews / proof).",
        "legal": ["privacy", "terms"],
        "style": "direct",
        "social_proof_weight": "high",
        "portfolio_weight": "medium",
        "cta_tone": "direct",
    },
    "GB": {
        "label": "United Kingdom",
        "reason_ru": "Прямой CTA, privacy-first, чёткие доказательства.",
        "legal": ["privacy", "terms"],
        "style": "direct",
        "social_proof_weight": "high",
        "portfolio_weight": "medium",
        "cta_tone": "direct",
    },
}


def decide_localization(*, market_code: str, package_id: str = "business") -> dict[str, Any]:
    code = (market_code or "DE").strip().upper() or "DE"
    pack = MARKET_PACKS.get(code) or {
        "label": f"Market {code}",
        "reason_ru": "Нейтральная локализация под рынок.",
        "legal": [],
        "style": "neutral",
        "social_proof_weight": "medium",
        "portfolio_weight": "medium",
        "cta_tone": "neutral",
    }
    return {
        "engine": ENGINE_ID,
        "role": "Localization Director",
        "choice": pack["label"],
        "market_code": code,
        "reason_ru": pack["reason_ru"],
        "reason_en": pack["reason_ru"],
        "apply": {
            "market_code": code,
            "legal_pack": list(pack.get("legal") or []),
            "style": pack.get("style"),
            "social_proof_weight": pack.get("social_proof_weight"),
            "portfolio_weight": pack.get("portfolio_weight"),
            "cta_tone": pack.get("cta_tone"),
            "package_id": (package_id or "business").lower(),
        },
    }


def localization_director_css(decision: dict[str, Any]) -> str:
    apply = decision.get("apply") or {}
    style = str(apply.get("style") or "neutral")
    tone = str(apply.get("cta_tone") or "neutral")
    portfolio = str(apply.get("portfolio_weight") or "medium")
    social = str(apply.get("social_proof_weight") or "medium")
    return f"""
/* Localization Director — {apply.get('market_code')} / {style} */
body[data-locale-style="{style}"] {{
  --locale-cta-weight: {"700" if tone == "direct" else "600"};
}}
body[data-locale-style="strict"] .section h2 {{ letter-spacing: -0.02em; }}
body[data-locale-style="editorial"] #gallery,
body[data-locale-portfolio="high"] #gallery {{
  padding-top: 4rem;
  padding-bottom: 4rem;
}}
body[data-locale-social="high"] #trust,
body[data-locale-social="high"] #testimonials {{
  padding-top: 3.5rem;
}}
body[data-locale-style="direct"] .btn,
body[data-locale-style="direct"] .topbar-cta {{
  font-weight: var(--locale-cta-weight);
  text-transform: none;
}}
body[data-locale-portfolio="{portfolio}"] {{ --portfolio-emphasis: {portfolio}; }}
body[data-locale-social="{social}"] {{ --social-emphasis: {social}; }}
"""


def apply_localization_html(html: str, decision: dict[str, Any]) -> str:
    import re

    apply = decision.get("apply") or {}
    style = str(apply.get("style") or "neutral")
    portfolio = str(apply.get("portfolio_weight") or "medium")
    social = str(apply.get("social_proof_weight") or "medium")
    code = str(apply.get("market_code") or "DE")
    legal = ",".join(str(x) for x in (apply.get("legal_pack") or []))

    extras = [
        f'data-locale-style="{style}"',
        f'data-locale-portfolio="{portfolio}"',
        f'data-locale-social="{social}"',
        f'data-locale-market="{code}"',
    ]
    if legal:
        extras.append(f'data-locale-legal="{legal}"')

    def _body(m):
        tag = m.group(0)
        add = " ".join(e for e in extras if e.split("=")[0] not in tag)
        return tag if not add else tag[:-1] + " " + add + ">"

    return re.sub(r"<body\b[^>]*>", _body, html, count=1, flags=re.I)
