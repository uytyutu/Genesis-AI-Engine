"""Deterministic CSS-motion pack for Classic Factory (no LLM).

When motion_level == "css", landings link assets/motion_kit.css + assets/reveal.js
and get hero/reveal class hooks. 3d_premium is gated elsewhere (waitlist).
"""

from __future__ import annotations

import shutil
from pathlib import Path

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
MOTION_KIT_NAME = "motion_kit.css"
REVEAL_JS_NAME = "reveal.js"

_HEAD_SNIPPET = (
    '  <link rel="stylesheet" href="assets/motion_kit.css">\n'
    "</head>"
)
_BODY_SNIPPET = '  <script src="assets/reveal.js" defer></script>\n</body>'


def motion_assets_dir() -> Path:
    return _ASSETS_DIR


def write_motion_assets(target_dir: Path) -> list[str]:
    """Copy motion_kit.css + reveal.js into target_dir/assets/. Returns relative paths."""
    assets = Path(target_dir) / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name in (MOTION_KIT_NAME, REVEAL_JS_NAME):
        src = _ASSETS_DIR / name
        if not src.is_file():
            raise FileNotFoundError(f"motion asset missing: {src}")
        dest = assets / name
        shutil.copy2(src, dest)
        written.append(f"assets/{name}")
    return written


def apply_css_motion_markup(html: str) -> str:
    """Inject asset links + hero/reveal class hooks into Classic HTML."""
    if "assets/motion_kit.css" in html and "class=\"reveal" in html:
        return html
    out = html

    # Hero entrance
    out = out.replace("<header class=\"hero\">", "<header class=\"hero\">", 1)
    out = out.replace("<h1", '<h1 class="hero-text"', 1)
    # If h1 already has class="large"
    out = out.replace(
        '<h1 class="hero-text" class="large"',
        '<h1 class="hero-text large"',
        1,
    )
    out = out.replace(
        '<h1 class="large"',
        '<h1 class="hero-text large"',
        1,
    )
    # Subtitle + trust + CTAs
    # First hero <p> after h1
    if 'class="hero-text hero-text-delay"' not in out:
        # Replace first subtitle paragraph inside hero — pattern: </h1>\n    <p>
        out = out.replace("</h1>\n    <p>", '</h1>\n    <p class="hero-text hero-text-delay">', 1)
        out = out.replace("</h1>\n<p>", '</h1>\n<p class="hero-text hero-text-delay">', 1)
    out = out.replace(
        '<div class="trust-row">',
        '<div class="trust-row hero-text hero-text-delay-2">',
        1,
    )
    out = out.replace('<a class="btn"', '<a class="btn cta-button"', 1)

    # Scroll reveal on main sections
    replacements = (
        ('<section class="section" id="services">', '<section class="section reveal" id="services">'),
        ('<section class="section benefits">', '<section class="section benefits reveal">'),
        ('<section class="section about">', '<section class="section about reveal">'),
        ('<section class="section" id="contact">', '<section class="section reveal" id="contact">'),
        ('<section class="section maps"', '<section class="section maps reveal"'),
        ('<section class="section testimonials"', '<section class="section testimonials reveal"'),
        ('<section class="section calculator"', '<section class="section calculator reveal"'),
    )
    for old, new in replacements:
        if old in out and new not in out:
            out = out.replace(old, new, 1)

    if "assets/motion_kit.css" not in out and "</head>" in out:
        out = out.replace("</head>", _HEAD_SNIPPET, 1)
    if "assets/reveal.js" not in out and "</body>" in out:
        out = out.replace("</body>", _BODY_SNIPPET, 1)
    return out


def inject_css_motion(html: str) -> str:
    """Alias used by engines — markup only; caller must write_motion_assets()."""
    return apply_css_motion_markup(html)
