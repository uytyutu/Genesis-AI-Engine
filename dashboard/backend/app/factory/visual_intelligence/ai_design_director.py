"""AI Design Director — Digital Experience Factory scoring.

Not a website generator scorecard: experience, mobile-first, creativity, luxury mode.
Official Acceptance: Starter < Business < Premium recognizable in 5 seconds (no price tags).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

# Industry Intelligence — niche experience (not just copy)
NICHE_IDENTITY: dict[str, dict[str, str]] = {
    "dental": {
        "theme": "premium_medical",
        "feel_ru": "чистый Premium Medical — светлый, спокойный, доверие",
        "hero_bias": "photo_calm",
    },
    "psychology": {
        "theme": "calm_clinical",
        "feel_ru": "спокойствие и контакт — светлая палитра, портрет специалиста, без эффектов ради эффектов",
        "hero_bias": "photo_portrait_calm",
    },
    "beauty": {
        "theme": "luxury",
        "feel_ru": "Luxury — мягкий свет, премиальная типографика",
        "hero_bias": "photo_luxury",
    },
    "restaurant": {
        "theme": "warm_atmosphere",
        "feel_ru": "тёплый атмосферный — еда, свет, уют, бронирование",
        "hero_bias": "video_food",
    },
    "handwerk": {
        "theme": "industrial",
        "feel_ru": "индустриальный — сила, материал, ясность",
        "hero_bias": "photo_large",
    },
    "auto": {
        "theme": "industrial_dynamic",
        "feel_ru": "динамика, тёмная тема, крупные фото",
        "hero_bias": "photo_dynamic",
    },
    "computer": {
        "theme": "tech",
        "feel_ru": "Tech — современный, сетка, умеренное свечение",
        "hero_bias": "svg_tech",
    },
    "it": {
        "theme": "tech",
        "feel_ru": "Tech — современный, сетка, умеренное свечение",
        "hero_bias": "svg_tech",
    },
    "law": {
        "theme": "trust_corporate",
        "feel_ru": "строгая типографика, спокойный motion, доверие",
        "hero_bias": "photo_trust",
    },
    "fitness": {
        "theme": "energy",
        "feel_ru": "энергия — контраст, движение, мотивация",
        "hero_bias": "photo_energy",
    },
}

PREMIUM_FEELING_THRESHOLD = 80
FIRST_IMPRESSION_PREMIUM_THRESHOLD = 90
SIMILARITY_REBUILD_THRESHOLD = 92
ENGINE_ID = "ai_design_director_v2"
PRODUCT_NAME = "Digital Experience Factory"

ACCEPTANCE_5S_RU = (
    "Если показать три версии рядом без ценников, человек должен почти всегда "
    "понять, где Starter, где Business и где Premium."
)


def _clip(n: float) -> int:
    return max(0, min(100, int(round(n))))


def _structural_fingerprint(html: str) -> str:
    """Coarse structure for Similarity (layouts, not copy)."""
    body_m = re.search(r"<body\b([^>]*)>", html, re.I)
    body_attrs = body_m.group(1) if body_m else ""
    hero = re.search(r"\bdata-hero-layout=[\"']([^\"']+)[\"']", body_attrs, re.I)
    layout = re.search(r"\bdata-layout-profile=[\"']([^\"']+)[\"']", body_attrs, re.I)
    sections = re.findall(r"<section\b[^>]*\bid=[\"']([^\"']+)[\"']", html, re.I)
    classes = re.findall(
        r'class=["\']([^"\']*(?:hero|mid-cta|trust|showcase|stats)[^"\']*)["\']',
        html,
        re.I,
    )
    raw = "|".join(
        [
            (hero.group(1) if hero else "-"),
            (layout.group(1) if layout else "-"),
            ",".join(sections[:12]),
            ",".join(sorted({c.split()[0] for c in classes})[:20]),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8", errors="replace")).hexdigest()[:16]


def similarity_pct(fp_a: str, fp_b: str) -> int:
    if not fp_a or not fp_b:
        return 0
    if fp_a == fp_b:
        return 100
    # Hamming-ish on hex nibbles
    same = sum(1 for x, y in zip(fp_a, fp_b) if x == y)
    return _clip(100.0 * same / max(len(fp_a), 1))


def score_html(
    html: str,
    *,
    package_id: str = "business",
    niche: str | None = None,
    luxury_mode: bool | None = None,
) -> dict[str, Any]:
    """Experience + craft scores from shipped HTML markers."""
    pid = (package_id or "business").lower()
    niche_key = (niche or "").lower()
    luxury = bool(luxury_mode) if luxury_mode is not None else pid == "premium"
    identity = NICHE_IDENTITY.get(niche_key) or {
        "theme": "modern_default",
        "feel_ru": "современный нейтральный",
        "hero_bias": "photo",
    }

    body = ""
    m_body = re.search(r"<body\b([^>]*)>", html, re.I)
    if m_body:
        body = m_body.group(1)

    has_tier = f'data-tier="{pid}"' in body or f"data-tier='{pid}'" in body
    has_hero = bool(re.search(r"\bdata-hero-layout=", body, re.I)) or bool(
        re.search(r'class=["\'][^"\']*\bhero\b', html, re.I)
    )
    has_layout = "data-layout-profile=" in body
    has_vie = "data-vie-engine=" in body
    has_motion = "data-motion=" in body or "motion" in html.lower()[:8000]
    font_links = len(re.findall(r"fonts\.googleapis|font-face|@import.*font", html, re.I))
    kpi = len(re.findall(r"hero-kpi|trust-bar|stats-strip|showcase", html, re.I))
    media_rich = len(
        re.findall(r"<video\b|lottie|three\.js|webgl|canvas\b|hero.*video", html, re.I)
    )
    has_cta = bool(re.search(r"\bbtn\b|mid-cta|contact|whatsapp", html, re.I))
    has_viewport = "viewport" in html.lower()
    has_responsive_css = bool(
        re.search(r"@media[^{]+max-width|clamp\(|vw\b|rem\b", html, re.I)
    )
    img_lazy = len(re.findall(r"loading=[\"']lazy[\"']", html, re.I))
    img_total = len(re.findall(r"<img\b", html, re.I))

    # Craft scores
    visual = 40.0
    if has_tier:
        visual += 15
    if has_vie:
        visual += 15
    if has_layout:
        visual += 10
    if kpi >= 2:
        visual += 10
    if pid == "premium":
        visual += 8 if media_rich or luxury else -10

    typography = 55.0 + min(35, font_links * 12)
    if "font-family" in html:
        typography += 10

    motion = 45.0
    if has_motion:
        motion += 20
    if pid in ("business", "premium"):
        motion += 10 if "transition" in html or "animation" in html else -5
    if pid == "premium" and (media_rich or luxury):
        motion += 12

    premium_feeling = 35.0
    if has_hero:
        premium_feeling += 15
    if has_vie:
        premium_feeling += 10
    if kpi >= 2:
        premium_feeling += 10
    if pid == "basic":
        premium_feeling = min(premium_feeling + 25, 72)
    elif pid == "business":
        premium_feeling += 15 if has_layout else 0
        premium_feeling += 10 if kpi else 0
    else:
        premium_feeling += 15 if has_layout and has_vie else 0
        premium_feeling += 20 if luxury else 0
        premium_feeling += 10 if media_rich else -15
        premium_feeling += 8 if font_links else 0

    # Experience Engine
    first_impression = 40.0
    if has_hero:
        first_impression += 25
    if has_layout:
        first_impression += 10
    if has_vie:
        first_impression += 10
    if pid == "premium" and luxury:
        first_impression += 10
    if pid == "basic":
        first_impression = min(first_impression + 15, 88)

    brand_emotion = 50.0
    if niche_key in NICHE_IDENTITY:
        brand_emotion += 20
    if has_layout:
        brand_emotion += 10
    if pid != "basic" and kpi:
        brand_emotion += 10

    trust = 45.0
    if "trust" in html.lower() or kpi:
        trust += 20
    if "impressum" in html.lower() or "datenschutz" in html.lower() or "privacy" in html.lower():
        trust += 15
    if has_cta:
        trust += 10

    conversion = 40.0
    if has_cta:
        conversion += 25
    if "form" in html.lower() or "whatsapp" in html.lower():
        conversion += 15
    if "mid-cta" in html.lower():
        conversion += 10

    # Mobile First Director (heuristic from markup signals)
    mobile = 35.0
    if has_viewport:
        mobile += 25
    if has_responsive_css:
        mobile += 20
    if img_total and img_lazy / max(img_total, 1) >= 0.3:
        mobile += 10
    if has_cta:
        mobile += 10

    creativity = 40.0
    if has_layout and has_hero:
        creativity += 20
    if has_vie:
        creativity += 10
    fingerprint = _structural_fingerprint(html)
    # unique-looking structure bits
    creativity += min(25, len(set(fingerprint)) * 2)

    scores = {
        "visual": _clip(visual),
        "typography": _clip(typography),
        "motion": _clip(motion),
        "premium_feeling": _clip(premium_feeling),
        "first_impression": _clip(first_impression),
        "brand_emotion": _clip(brand_emotion),
        "trust": _clip(trust),
        "conversion_readiness": _clip(conversion),
        "mobile_experience": _clip(mobile),
        "creativity": _clip(creativity),
    }

    overall = _clip(
        scores["first_impression"] * 0.22
        + scores["premium_feeling"] * 0.18
        + scores["trust"] * 0.12
        + scores["conversion_readiness"] * 0.12
        + scores["mobile_experience"] * 0.12
        + scores["visual"] * 0.08
        + scores["typography"] * 0.06
        + scores["motion"] * 0.05
        + scores["creativity"] * 0.05
    )

    recommendations: list[str] = []
    if scores["first_impression"] < FIRST_IMPRESSION_PREMIUM_THRESHOLD and pid == "premium":
        recommendations.append(
            f"First Impression {scores['first_impression']} < {FIRST_IMPRESSION_PREMIUM_THRESHOLD} — Premium Gate FAIL; rebuild Hero"
        )
    if scores["premium_feeling"] < PREMIUM_FEELING_THRESHOLD and pid == "premium":
        recommendations.append("Premium Feeling below threshold — Luxury Mode composition")
    if scores["mobile_experience"] < 80:
        recommendations.append("Mobile First Director — fix hero crop / CTA / images")
    if scores["conversion_readiness"] < 75:
        recommendations.append("Strengthen Conversion Readiness (CTA / form / WhatsApp)")
    if scores["creativity"] < 60:
        recommendations.append("Raise Creativity — alternate Hero / blocks / palette")
    if not recommendations and overall >= 85:
        recommendations.append("Hold — candidate for 5-second blind tier test")

    ok = True
    if pid == "premium":
        ok = (
            scores["premium_feeling"] >= PREMIUM_FEELING_THRESHOLD
            and scores["first_impression"] >= FIRST_IMPRESSION_PREMIUM_THRESHOLD
        )
    elif pid == "business":
        ok = overall >= 70 and has_vie and scores["first_impression"] >= 75
    else:
        ok = overall >= 55 and has_tier

    return {
        "engine": ENGINE_ID,
        "product": PRODUCT_NAME,
        "ok": ok,
        "overall": overall,
        "scores": scores,
        "threshold_premium_feeling": PREMIUM_FEELING_THRESHOLD,
        "threshold_first_impression_premium": FIRST_IMPRESSION_PREMIUM_THRESHOLD,
        "package_id": pid,
        "niche": niche_key or None,
        "luxury_mode": luxury,
        "identity": identity,
        "fingerprint": fingerprint,
        "markers": {
            "data_tier_ok": has_tier,
            "hero": has_hero,
            "layout_profile": has_layout,
            "vie": has_vie,
            "font_signals": font_links,
            "kpi_trust_signals": kpi,
            "rich_media_signals": media_rich,
            "viewport": has_viewport,
            "responsive_css": has_responsive_css,
        },
        "recommendations": recommendations[:8],
        "acceptance_5s_ru": ACCEPTANCE_5S_RU,
        "rule_ru": "Клиент должен узнать Virtus Core по качеству, а не по шаблону.",
    }


def score_demo_path(
    path: Path,
    *,
    package_id: str,
    niche: str,
) -> dict[str, Any]:
    html = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    out = score_html(html, package_id=package_id, niche=niche)
    out["path"] = str(path)
    out["exists"] = path.is_file()
    return out


def audit_design_director_gallery(root: Path | None = None) -> dict[str, Any]:
    """5-second Acceptance: dental Starter / Business / Premium side-by-side."""
    from app.integration.demo_gallery_audit import _previews_root

    root = root or _previews_root()
    samples = [
        ("basic", "dental"),
        ("business", "dental"),
        ("premium", "dental"),
    ]
    rows: list[dict[str, Any]] = []
    for tier, niche in samples:
        path = root / "sites" / tier / niche / "index.html"
        rows.append(score_demo_path(path, package_id=tier, niche=niche))

    scores = [r["overall"] for r in rows if r.get("exists")]
    fi = [r["scores"]["first_impression"] for r in rows if r.get("exists")]
    # Strict ladder: Starter < Business < Premium on overall OR first_impression
    ladder_overall = False
    ladder_fi = False
    if len(scores) >= 3:
        ladder_overall = scores[0] < scores[1] < scores[2]
        ladder_fi = fi[0] < fi[1] < fi[2]
    five_second_pass = ladder_overall or ladder_fi

    # Creative Score / Similarity between Business and Premium (same niche)
    sim_bp = 0
    if len(rows) >= 3 and rows[1].get("fingerprint") and rows[2].get("fingerprint"):
        sim_bp = similarity_pct(rows[1]["fingerprint"], rows[2]["fingerprint"])
    rebuild_needed = sim_bp >= SIMILARITY_REBUILD_THRESHOLD

    premium_row = next((r for r in rows if r.get("package_id") == "premium"), None)
    premium_ok = bool(premium_row and premium_row.get("ok"))

    ok = five_second_pass and premium_ok and not rebuild_needed
    return {
        "id": "ai_design_director",
        "title": "AI Design Director",
        "product": PRODUCT_NAME,
        "engine": ENGINE_ID,
        "ok": ok,
        "status": "PASS" if ok else "FAIL",
        "mark": "🟢" if ok else "🔴",
        "acceptance_5s": {
            "criterion_ru": ACCEPTANCE_5S_RU,
            "pass": five_second_pass,
            "ladder_overall": ladder_overall,
            "ladder_first_impression": ladder_fi,
            "overall_scores": scores,
            "first_impression_scores": fi,
        },
        "creative_score": {
            "business_premium_similarity_pct": sim_bp,
            "rebuild_if_similarity_gte": SIMILARITY_REBUILD_THRESHOLD,
            "rebuild_needed": rebuild_needed,
        },
        "differentiated": five_second_pass,
        "samples": rows,
        "roadmap": [
            "Experience Engine — First Impression / Trust / Conversion",
            "Mobile First Director",
            "Industry Intelligence",
            "AI Creative Score + Similarity rebuild",
            "Luxury Mode (Premium)",
            "Visual Identity / Typography / Motion / Hero / Components",
            "Store Experience parity + auth",
        ],
        "ssot_ru": (
            "Digital Experience Factory. Узнаваемость по качеству. "
            "5 секунд без ценников = Acceptance. Horizon — после Factory + Store."
        ),
    }
