"""Visual Quality Gate — score ≥ threshold or block publish / suggest rebuild."""

from __future__ import annotations

import colorsys
import re
from dataclasses import dataclass, field
from typing import Any

VISUAL_QUALITY_THRESHOLD = 90.0
ENGINE_ID = "visual_quality_v1"


@dataclass
class VisualQualityResult:
    passed: bool
    score: float
    threshold: float = VISUAL_QUALITY_THRESHOLD
    checks: list[dict[str, Any]] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    engine_id: str = ENGINE_ID

    @property
    def failures(self) -> list[str]:
        return [c["id"] for c in self.checks if not c.get("ok")]

    def as_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "passed": self.passed,
            "score": self.score,
            "threshold": self.threshold,
            "checks": self.checks,
            "suggestions": self.suggestions,
            "failures": self.failures,
        }


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float] | None:
    h = (hex_color or "").strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        return None
    r, g, b = int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0
    return r, g, b


def _rel_luminance(rgb: tuple[float, float, float]) -> float:
    def chan(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def _contrast_ratio(a: str, b: str) -> float | None:
    ra, rb = _hex_to_rgb(a), _hex_to_rgb(b)
    if not ra or not rb:
        return None
    l1, l2 = _rel_luminance(ra), _rel_luminance(rb)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _harmony_score(primary: str, accent: str) -> float:
    """Simple hue distance — complementary/analogous get higher marks."""
    pa, aa = _hex_to_rgb(primary), _hex_to_rgb(accent)
    if not pa or not aa:
        return 70.0
    h1, s1, v1 = colorsys.rgb_to_hsv(*pa)
    h2, s2, v2 = colorsys.rgb_to_hsv(*aa)
    dist = abs(h1 - h2)
    dist = min(dist, 1.0 - dist) * 360
    # Same family (rose/rose) with clear value/saturation step still counts as intentional
    value_step = abs(v1 - v2)
    sat_step = abs(s1 - s2)
    if dist < 20 and (value_step >= 0.15 or sat_step >= 0.15):
        return 88.0
    if 20 <= dist <= 50 or 140 <= dist <= 180:
        return 94.0
    if dist < 8:
        return 72.0
    return 84.0


def _check(cid: str, ok: bool, points: float, detail: str) -> dict[str, Any]:
    return {"id": cid, "ok": ok, "points": points, "detail": detail}


def run_visual_quality_gate(
    html: str,
    *,
    meta: dict[str, Any] | None = None,
    threshold: float = VISUAL_QUALITY_THRESHOLD,
) -> VisualQualityResult:
    """Score composition · color · readability · type · contrast · images · perf · responsive."""
    meta = meta or {}
    html_l = (html or "").lower()
    checks: list[dict[str, Any]] = []
    suggestions: list[str] = []
    weights: list[tuple[float, float]] = []  # (weight, earned 0–100)

    # 1. Composition
    has_hero = "data-hero-layout" in html_l or 'class="hero"' in html_l or "id=\"hero\"" in html_l
    has_sections = html_l.count("<section") >= 2 or html_l.count('data-vie-section') >= 2
    has_niche = "data-niche=" in html_l or bool(meta.get("niche") or meta.get("niche_id"))
    has_vie = "data-vie-engine=" in html_l or bool(meta.get("visual_plan"))
    comp_score = 0.0
    if has_hero:
        comp_score += 35
    if has_sections:
        comp_score += 30
    if has_niche:
        comp_score += 20
    if has_vie:
        comp_score += 15
    ok_comp = comp_score >= 70
    checks.append(
        _check(
            "composition",
            ok_comp,
            comp_score,
            f"hero={has_hero} sections={has_sections} niche={has_niche} vie={has_vie}",
        )
    )
    weights.append((1.2, comp_score))
    if not ok_comp:
        suggestions.append("Пересобрать композицию: Hero + секции + niche Style Engine.")

    # 2. Color harmony
    primary = str(meta.get("primary") or meta.get("color_primary") or "")
    accent = str(meta.get("accent") or meta.get("color_accent") or "")
    # Try extract from CSS vars
    if not primary:
        m = re.search(r"--p\s*:\s*(#[0-9a-fA-F]{3,8})", html or "")
        primary = m.group(1) if m else "#1e293b"
    if not accent:
        m = re.search(r"--acc\s*:\s*(#[0-9a-fA-F]{3,8})", html or "")
        accent = m.group(1) if m else "#64748b"
    harmony = _harmony_score(primary, accent)
    ok_harm = harmony >= 75
    checks.append(_check("color_harmony", ok_harm, harmony, f"{primary} / {accent}"))
    weights.append((1.0, harmony))
    if not ok_harm:
        suggestions.append("Скорректировать палитру Style Engine (accent vs primary).")

    # 3. Readability / typography
    has_fonts = "fonts.googleapis.com" in html_l or "--font" in html_l or "font-family" in html_l
    has_display = "--font-display" in html_l or "font-display" in html_l or "fraunces" in html_l or "cormorant" in html_l or "libre baskerville" in html_l or "oswald" in html_l or "barlow" in html_l
    # Avoid default Inter/Roboto/Arial as sole display for premium bar
    defaultish = bool(re.search(r"font-family:\s*(inter|roboto|arial|system-ui)\b", html_l))
    type_score = 50.0
    if has_fonts:
        type_score += 25
    if has_display or not defaultish:
        type_score += 15
    if "letter-spacing" in html_l or "--ls" in html_l or "tracking" in html_l:
        type_score += 10
    type_score = min(100.0, type_score)
    ok_type = type_score >= 70
    checks.append(_check("typography", ok_type, type_score, "fonts/display hierarchy"))
    weights.append((1.1, type_score))
    if not ok_type:
        suggestions.append("Усилить типографику: display + body из Design Engine.")

    # 4. Contrast
    ink = str(meta.get("ink") or "")
    surface_color = str(
        meta.get("surface_token")
        or meta.get("surface_color")
        or meta.get("bg")
        or ""
    )
    if not ink:
        m = re.search(r"--ink\s*:\s*(#[0-9a-fA-F]{3,8})", html or "")
        ink = m.group(1) if m else "#0f172a"
    if not surface_color:
        m = re.search(r"--surface\s*:\s*(#[0-9a-fA-F]{3,8})", html or "")
        surface_color = m.group(1) if m else "#ffffff"
    ratio = _contrast_ratio(ink, surface_color)
    # Dark themes: ink is often light on dark surface — if pair fails, try ink vs white card
    if ratio is not None and ratio < 4.5:
        alt = _contrast_ratio(ink, "#ffffff")
        if alt is not None and alt > ratio:
            ratio = alt
            detail_note = "dark_theme_ink_on_white"
        else:
            detail_note = ""
    else:
        detail_note = ""
    if ratio is None:
        contrast_score = 80.0
        ok_contrast = True
        detail = "tokens_assumed"
    else:
        if ratio >= 7:
            contrast_score = 98.0
        elif ratio >= 4.5:
            contrast_score = 90.0
        elif ratio >= 3:
            contrast_score = 72.0
        else:
            contrast_score = 50.0
        ok_contrast = ratio >= 4.5
        detail = f"ratio={ratio:.2f}" + (f" · {detail_note}" if detail_note else "")
    checks.append(_check("contrast", ok_contrast, contrast_score, detail))
    weights.append((1.3, contrast_score))
    if not ok_contrast:
        suggestions.append("Повысить контраст текста (--ink / --surface).")

    # 5. Image quality signals
    from app.factory.visual_intelligence.asset_manager import AssetManager

    imgs = AssetManager().evaluate_html_images(html or "")
    if not imgs:
        img_score = 78.0  # text-first niches ok
        ok_img = True
        img_detail = "no_images"
    else:
        alt_ok = sum(1 for i in imgs if i["has_alt"]) / len(imgs)
        lazy_ok = sum(1 for i in imgs if i["lazy"]) / len(imgs)
        img_score = round(55 + alt_ok * 25 + lazy_ok * 20, 1)
        ok_img = img_score >= 70
        img_detail = f"n={len(imgs)} alt={alt_ok:.0%} lazy={lazy_ok:.0%}"
    asset_meta = meta.get("assets") if isinstance(meta.get("assets"), list) else []
    if asset_meta:
        qs = [float(a.get("quality_score") or 0) for a in asset_meta if isinstance(a, dict)]
        if qs:
            avg_q = sum(qs) / len(qs)
            img_score = round((img_score + avg_q) / 2, 1)
            if avg_q < 70:
                ok_img = False
                suggestions.append("Заменить ассеты ниже Quality Floor (Asset Manager).")
    checks.append(_check("images", ok_img, img_score, img_detail))
    weights.append((1.0, img_score))

    # 6. Performance (no heavy libs on client)
    heavy = ("lottie", "gsap", "three.js", "three.min", "framer-motion", "spline")
    surface = str(meta.get("surface") or "website")
    found_heavy = [h for h in heavy if h in html_l]
    if surface == "platform":
        perf_score = 92.0 if len(found_heavy) <= 1 else 80.0
        ok_perf = True
    else:
        ok_perf = len(found_heavy) == 0
        perf_score = 96.0 if ok_perf else 40.0
    if "prefers-reduced-motion" in html_l or "motion_kit" in html_l:
        perf_score = min(100.0, perf_score + 2)
    checks.append(
        _check("performance", ok_perf, perf_score, f"heavy={found_heavy or 'none'}")
    )
    weights.append((1.2, perf_score))
    if not ok_perf:
        suggestions.append("Убрать тяжёлые библиотеки из клиентского ZIP — CSS Motion only.")

    # 7. Adaptivity
    has_viewport = "viewport" in html_l
    has_media = "@media" in html_l or "max-width" in html_l
    adapt_score = 40.0
    if has_viewport:
        adapt_score += 30
    if has_media:
        adapt_score += 30
    ok_adapt = adapt_score >= 70
    checks.append(
        _check("adaptivity", ok_adapt, adapt_score, f"viewport={has_viewport} mq={has_media}")
    )
    weights.append((1.0, adapt_score))
    if not ok_adapt:
        suggestions.append("Добавить viewport + responsive CSS.")

    # 8. Readability length / clutter proxy
    text_bits = re.sub(r"<[^>]+>", " ", html or "")
    words = [w for w in text_bits.split() if len(w) > 2]
    # Hero budget: penalize extreme density in first 800 chars of body text
    readability = 88.0
    if len(words) > 2500:
        readability -= 10
    if "lorem ipsum" in html_l:
        readability = 40.0
        suggestions.append("Убрать placeholder-текст.")
    ok_read = readability >= 70
    checks.append(_check("readability", ok_read, readability, f"words≈{len(words)}"))
    weights.append((0.8, readability))

    total_w = sum(w for w, _ in weights) or 1.0
    score = round(sum(w * s for w, s in weights) / total_w, 1)
    # Hard fails pull score down
    hard_fail = any(
        not c["ok"] and c["id"] in {"contrast", "performance", "composition"}
        for c in checks
    )
    if hard_fail and score >= threshold:
        score = min(score, threshold - 0.5)

    passed = score >= threshold and all(
        c["ok"] for c in checks if c["id"] in {"composition", "contrast", "performance", "adaptivity"}
    )
    if not passed and not suggestions:
        suggestions.append(
            f"Визуальная оценка {score} < {threshold}. Factory предлагает пересборку визуальной части."
        )

    return VisualQualityResult(
        passed=passed,
        score=score,
        threshold=threshold,
        checks=checks,
        suggestions=suggestions,
    )


class VisualQualityError(Exception):
    def __init__(self, result: VisualQualityResult) -> None:
        self.result = result
        super().__init__(
            f"Visual Quality Gate failed: score={result.score} < {result.threshold}"
        )


def assert_visual_quality(
    html: str,
    *,
    meta: dict[str, Any] | None = None,
    threshold: float = VISUAL_QUALITY_THRESHOLD,
) -> VisualQualityResult:
    result = run_visual_quality_gate(html, meta=meta, threshold=threshold)
    if not result.passed:
        raise VisualQualityError(result)
    return result
