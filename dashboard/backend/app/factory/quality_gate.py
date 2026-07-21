"""Factory Quality Gate — commercial deliverable must PASS before client ZIP.

Categories: design · localization · SEO · accessibility · performance · brand.
Registry of checks — extend without rewriting pack/build flow.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Soft size caps for static Path A assets (bytes).
_MAX_INLINE_CSS = 220_000
_MAX_MOTION_CSS = 40_000
_MAX_REVEAL_JS = 24_000

_HEAVY_LIBS = (
    "gsap",
    "framer-motion",
    "framer",
    "three.js",
    "three.min",
    "jquery",
    "react.",
    "react-dom",
    "anime.min.js",
    "lottie",
)

_BRAND_LEAK = re.compile(
    r"Virtus(\s+Core)?|"
    r"\bResearch\b|"
    r"tier-switch|"
    r"Demo-Tarif|"
    r"Demonstration|"
    r"\bWatermark\b|"
    r"Genesis\.exe|"
    r"Mission Control|"
    r"Factory ·",
    re.IGNORECASE,
)

_LOCALIZATION_STUBS = (
    "lorem ipsum",
    "loremipsum",
    "todo:",
    "fixme",
    "your company",
    "sample text",
    "placeholder text",
    "demo content",
    "preview only",
    "[todo]",
    "tbd",
)

_ENGLISH_UI_STUBS = (
    "click here",
    "learn more",
    "get started",
    "lorem ipsum",
    "coming soon",
)


@dataclass(frozen=True)
class GateCheck:
    id: str
    category: str
    ok: bool
    detail: str = ""


@dataclass
class QualityGateResult:
    passed: bool
    checks: list[GateCheck] = field(default_factory=list)

    @property
    def failures(self) -> list[str]:
        return [
            f"{c.category}:{c.id}" + (f" — {c.detail}" if c.detail else "")
            for c in self.checks
            if not c.ok
        ]

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "failures": self.failures,
            "checks": [
                {
                    "id": c.id,
                    "category": c.category,
                    "ok": c.ok,
                    "detail": c.detail,
                }
                for c in self.checks
            ],
        }


class QualityGateError(ValueError):
    """Raised when client ZIP is blocked by the Quality Gate."""

    def __init__(self, result: QualityGateResult):
        self.result = result
        msg = "quality_gate_failed: " + "; ".join(result.failures[:8])
        super().__init__(msg)


def run_quality_gate(
    html: str,
    *,
    meta: dict | None = None,
    assets_dir: Path | None = None,
) -> QualityGateResult:
    """Evaluate Path A index.html (+ optional assets/) for commercial release."""
    meta = meta or {}
    checks: list[GateCheck] = []
    lower = html.lower()

    def add(category: str, cid: str, ok: bool, detail: str = "") -> None:
        checks.append(GateCheck(id=cid, category=category, ok=ok, detail=detail))

    # --- Design ---
    add("design", "hero_layout", bool(re.search(r'data-hero-layout="[A-F]"', html)), "data-hero-layout")
    add(
        "design",
        "component_profile",
        bool(re.search(r'data-comp-profile="[A-C]"', html)),
        "data-comp-profile",
    )
    add(
        "design",
        "market_profile",
        bool(re.search(r'data-market="[A-Z]{2}"', html)),
        "data-market",
    )
    add(
        "design",
        "niche_style",
        bool(re.search(r'data-niche="[a-z0-9_-]+"', html))
        and ("Niche Design System" in html or "--card-radius" in html or "--p:" in html),
        "data-niche + design tokens",
    )
    if meta.get("hero_layout") and meta.get("component_profile"):
        # Meta consistency when present
        add(
            "design",
            "meta_hero",
            f'data-hero-layout="{meta.get("hero_layout")}"' in html,
            "meta hero_layout matches HTML",
        )

    # --- Localization ---
    stub_hit = next((s for s in _LOCALIZATION_STUBS if s in lower), None)
    add("localization", "no_stubs", stub_hit is None, stub_hit or "")
    add("localization", "no_mustache", not bool(re.search(r"\{\{[^{}]+\}\}", html)), "{{…}}")
    add("localization", "no_ui_keys", not bool(re.search(r"\bui\.[a-z0-9_]+\b", html, re.I)), "ui.* keys")
    en_hit = next((s for s in _ENGLISH_UI_STUBS if s in lower), None)
    # Only enforce English-stub ban for non-EN markets
    market = str(meta.get("market_code") or _attr(html, "data-market") or "DE").upper()
    lang = _attr(html, "lang") or ""
    if market in ("DE", "AT", "FR", "ES", "NL") or lang in ("de", "fr", "es", "nl"):
        add("localization", "no_english_stubs", en_hit is None, en_hit or "")
    else:
        add("localization", "no_english_stubs", True, "skipped_en_market")

    # --- SEO ---
    add("seo", "lang", bool(re.search(r"<html[^>]+lang=", html, re.I)), "html lang")
    add("seo", "hreflang", 'rel="alternate"' in lower and "hreflang=" in lower, "hreflang")
    add("seo", "title", bool(re.search(r"<title>[^<]{3,}</title>", html, re.I)), "title")
    add(
        "seo",
        "description",
        'name="description"' in lower and bool(re.search(r'name="description"\s+content="[^"]{8,}"', html, re.I)),
        "meta description",
    )
    add("seo", "canonical", 'rel="canonical"' in lower, "canonical")
    # Schema / OG required for business+ extended SEO; soft for basic
    tier = str(meta.get("package_id") or _attr(html, "data-tier") or "basic").lower()
    if "package_delivery" in meta and isinstance(meta["package_delivery"], dict):
        tier = str(meta["package_delivery"].get("package_id") or tier).lower()
    if tier in ("business", "premium"):
        add("seo", "schema", "application/ld+json" in lower, "JSON-LD")
        add("seo", "og", "og:title" in lower and "og:locale" in lower, "Open Graph")
    else:
        add("seo", "schema", True, "optional_basic")
        add("seo", "og", True, "optional_basic")

    # --- Accessibility ---
    add(
        "accessibility",
        "lang_ok",
        bool(re.search(r'lang="(?:de|en|fr|es|nl|cs|uk|ru)"', lower)),
        "supported lang",
    )
    imgs = re.findall(r"<img\b[^>]*>", html, flags=re.I)
    imgs_ok = all(re.search(r"\balt=", img, re.I) for img in imgs) if imgs else True
    add("accessibility", "img_alt", imgs_ok, f"imgs={len(imgs)}")
    add("accessibility", "h1", bool(re.search(r"<h1\b", html, re.I)), "h1 present")
    add("accessibility", "heading_order", _heading_order_ok(html), "h1 before h2/h3")
    add(
        "accessibility",
        "aria_or_labels",
        "aria-label" in lower or "aria-hidden" in lower or "<summary" in lower,
        "aria/summary",
    )
    add(
        "accessibility",
        "reduced_motion",
        "prefers-reduced-motion" in lower
        or 'href="assets/motion_kit.css"' in lower
        or (
            assets_dir is not None
            and _file_contains(assets_dir / "motion_kit.css", "prefers-reduced-motion")
        )
        or (_attr(html, "data-motion") or "none") == "none",
        "reduced-motion support",
    )
    add(
        "accessibility",
        "contrast_tokens",
        "--ink" in html or "color: var(--ink)" in html or "color:var(--ink)" in lower,
        "--ink token",
    )

    # --- Performance ---
    heavy = next((lib for lib in _HEAVY_LIBS if lib in lower), None)
    add("performance", "no_heavy_libs", heavy is None, heavy or "")
    lazy_ok = True
    for img in imgs:
        src = re.search(r'src="([^"]+)"', img, re.I)
        if not src:
            continue
        path = src.group(1).lower()
        # Hero/logo/favicon are above-the-fold brand assets — skip lazy requirement.
        if "hero" in path or "logo" in path or "favicon" in path:
            continue
        if "loading=" not in img.lower():
            lazy_ok = False
            break
    add("performance", "lazy_images", lazy_ok, "non-hero images")
    motion = _attr(html, "data-motion") or "none"
    if motion == "css":
        add(
            "performance",
            "motion_killswitch",
            "prefers-reduced-motion" in lower
            or 'href="assets/motion_kit.css"' in lower
            or (
                assets_dir is not None
                and _file_contains(assets_dir / "motion_kit.css", "prefers-reduced-motion")
            ),
            "motion css/js",
        )
    else:
        add("performance", "motion_killswitch", True, "motion_none")

    style_blocks = re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.I | re.S)
    inline_css_len = sum(len(b) for b in style_blocks)
    add(
        "performance",
        "css_budget",
        inline_css_len <= _MAX_INLINE_CSS,
        f"{inline_css_len}B",
    )
    if assets_dir is not None:
        mcss = assets_dir / "motion_kit.css"
        rjs = assets_dir / "reveal.js"
        if mcss.is_file():
            sz = mcss.stat().st_size
            add("performance", "motion_css_budget", sz <= _MAX_MOTION_CSS, f"{sz}B")
        else:
            add("performance", "motion_css_budget", motion != "css", "missing")
        if rjs.is_file():
            sz = rjs.stat().st_size
            add("performance", "js_budget", sz <= _MAX_REVEAL_JS, f"{sz}B")
            js_text = rjs.read_text(encoding="utf-8", errors="ignore").lower()
            heavy_js = next((lib for lib in _HEAVY_LIBS if lib in js_text), None)
            add("performance", "js_no_heavy", heavy_js is None, heavy_js or "")
        else:
            add("performance", "js_budget", motion != "css", "missing")
            add("performance", "js_no_heavy", True, "no_js")
    else:
        add("performance", "motion_css_budget", True, "assets_not_checked")
        add("performance", "js_budget", True, "assets_not_checked")
        add("performance", "js_no_heavy", True, "assets_not_checked")

    # --- Brand ---
    brand_hit = _BRAND_LEAK.search(html)
    add(
        "brand",
        "no_platform_chrome",
        brand_hit is None,
        brand_hit.group(0) if brand_hit else "",
    )
    demo_hit = bool(re.search(r"\b(demo|preview)\b", html, re.I))
    add("brand", "no_demo_preview_words", not demo_hit, "demo|preview")

    passed = all(c.ok for c in checks)
    return QualityGateResult(passed=passed, checks=checks)


def assert_quality_gate(
    html: str,
    *,
    meta: dict | None = None,
    assets_dir: Path | None = None,
) -> QualityGateResult:
    result = run_quality_gate(html, meta=meta, assets_dir=assets_dir)
    if not result.passed:
        raise QualityGateError(result)
    return result


def _attr(html: str, name: str) -> str | None:
    # body/html attributes
    m = re.search(rf'\b{re.escape(name)}="([^"]*)"', html, flags=re.I)
    return m.group(1) if m else None


def _heading_order_ok(html: str) -> bool:
    heads = re.findall(r"<h([1-6])\b", html, flags=re.I)
    if not heads:
        return False
    if heads[0] != "1":
        return False
    return "1" in heads


def _file_contains(path: Path, needle: str) -> bool:
    try:
        return needle in path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
