"""R3.2.1 — UX Polish for Path A Factory landings.

Document scroll hygiene + tiered back-to-top button.
No architecture change. No LLM.
"""

from __future__ import annotations

import shutil
from pathlib import Path

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
UX_JS_NAME = "ux_polish.js"


def write_ux_polish_assets(target_dir: Path) -> list[str]:
    """Copy ux_polish.js into product assets/. Always safe to call."""
    assets = Path(target_dir) / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    src = _ASSETS_DIR / UX_JS_NAME
    if not src.is_file():
        raise FileNotFoundError(f"ux polish asset missing: {src}")
    dest = assets / UX_JS_NAME
    shutil.copy2(src, dest)
    return [f"assets/{UX_JS_NAME}"]


def ux_polish_enabled(tier: str | None) -> bool:
    t = (tier or "basic").strip().lower()
    return t in ("business", "premium")


def ux_polish_css(tier: str | None) -> str:
    """CSS: natural page scroll + back-to-top (Business simple / Premium animated)."""
    t = (tier or "basic").strip().lower()
    lines = [
        "    /* R3.2.1 UX Polish — document scroll */",
        "    html { scroll-behavior: smooth; }",
        "    @media (prefers-reduced-motion: reduce) {",
        "      html { scroll-behavior: auto; }",
        "    }",
        "    html, body {",
        "      max-width: 100%;",
        "      overflow-x: clip;",
        "    }",
        "    body { min-height: 100%; }",
        "    /* Prefer window scroll — avoid nested page shells */",
        "    .site-shell, .page-wrap, main.site-main {",
        "      overflow: visible;",
        "      height: auto;",
        "      max-height: none;",
        "    }",
    ]
    if t not in ("business", "premium"):
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            "    .back-to-top {",
            "      position: fixed;",
            "      right: max(1rem, env(safe-area-inset-right));",
            "      bottom: max(1.15rem, env(safe-area-inset-bottom));",
            "      z-index: 40;",
            "      width: 2.75rem;",
            "      height: 2.75rem;",
            "      border-radius: 999px;",
            "      display: grid;",
            "      place-items: center;",
            "      text-decoration: none;",
            "      border: 1px solid var(--line, #e2e8f0);",
            "      background: #ffffff;",
            "      color: var(--pd, #0f172a);",
            "      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);",
            "      opacity: 0;",
            "      visibility: hidden;",
            "      pointer-events: none;",
            "      transform: translateY(10px);",
            "      transition: opacity 0.28s ease, transform 0.28s ease, visibility 0.28s, box-shadow 0.2s;",
            "      -webkit-tap-highlight-color: transparent;",
            "    }",
            "    .back-to-top.is-visible {",
            "      opacity: 1;",
            "      visibility: visible;",
            "      pointer-events: auto;",
            "      transform: translateY(0);",
            "    }",
            "    .back-to-top:focus-visible {",
            "      outline: 2px solid var(--acc, #38bdf8);",
            "      outline-offset: 3px;",
            "    }",
            "    .back-to-top svg { width: 1.15rem; height: 1.15rem; display: block; }",
            "    @media (max-width: 720px) {",
            "      .back-to-top { width: 2.55rem; height: 2.55rem; }",
            "    }",
        ]
    )
    if t == "premium":
        lines.extend(
            [
                "    body[data-tier=\"premium\"] .back-to-top {",
                "      background: #1c1917;",
                "      color: #fafaf9;",
                "      border-color: rgba(197, 165, 114, 0.45);",
                "      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);",
                "    }",
                "    body[data-tier=\"premium\"] .back-to-top:hover {",
                "      transform: translateY(-3px);",
                "      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.42);",
                "      border-color: rgba(197, 165, 114, 0.75);",
                "    }",
                "    body[data-tier=\"premium\"] .back-to-top.is-visible:hover {",
                "      transform: translateY(-3px);",
                "    }",
            ]
        )
    else:
        lines.extend(
            [
                "    body[data-tier=\"business\"] .back-to-top:hover {",
                "      transform: translateY(-2px);",
                "      box-shadow: 0 10px 28px rgba(15, 23, 42, 0.16);",
                "    }",
                "    body[data-tier=\"business\"] .back-to-top.is-visible:hover {",
                "      transform: translateY(-2px);",
                "    }",
            ]
        )
    lines.extend(
        [
            "    @media (prefers-reduced-motion: reduce) {",
            "      .back-to-top {",
            "        transition: opacity 0.15s ease, visibility 0.15s;",
            "        transform: none !important;",
            "      }",
            "    }",
        ]
    )
    return "\n".join(lines) + "\n"


def back_to_top_html(tier: str | None, *, label: str = "Nach oben") -> str:
    if not ux_polish_enabled(tier):
        return ""
    safe = (label or "Nach oben").replace('"', "&quot;")
    return (
        f'  <a class="back-to-top" href="#top" aria-label="{safe}" aria-hidden="true">'
        f'<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
        f'<path fill="currentColor" d="M12 5.5 5.8 11.7l1.4 1.4L11 9.3V19h2V9.3l3.8 3.8 1.4-1.4z"/>'
        f"</svg></a>\n"
    )


def back_to_top_script_tag(tier: str | None) -> str:
    if not ux_polish_enabled(tier):
        return ""
    return '  <script src="assets/ux_polish.js" defer></script>\n'
