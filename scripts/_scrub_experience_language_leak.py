"""Strip leaked experience_language JS (visible as page text) and fix topbar contrast on public demos."""
from __future__ import annotations

import re
from pathlib import Path

PREVIEWS = Path(__file__).resolve().parents[1] / "dashboard" / "frontend" / "public" / "package-previews"
NICHES = [
    "beauty",
    "cleaning",
    "it_support",
    "dental",
    "restaurant",
    "handwerk",
    "law",
    "auto",
]

# Bare JS blocks that were injected without <script> tags (client-visible).
LEAK_RE = re.compile(
    r"(?ms)^\s*/\*\s*Virtus Core experience_language\s*\*/\s*"
    r"\(function\s*\(\)\s*\{.*?\}\)\s*\(\)\s*;\s*"
)

CONTRAST_CSS = """
<style id="vitrine-contrast-fix">
/* Public demos: never blend brand/nav into light header */
.topbar,
header.topbar,
body[data-dna-style] .topbar {
  background: rgba(12, 16, 22, 0.92) !important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255,255,255,0.12);
}
.topbar .brand-word,
.topbar .brand strong,
.topbar a:not(.btn):not(.topbar-cta):not(.cta-button),
.topbar-links a,
body[data-dna-style] .topbar a:not(.btn):not(.topbar-cta):not(.cta-button) {
  color: #f4f6f8 !important;
  text-shadow: none !important;
  opacity: 1 !important;
}
.topbar a:not(.btn):not(.topbar-cta):hover {
  color: #ffffff !important;
  opacity: 1 !important;
}
.topbar-social {
  color: #f4f6f8 !important;
  border-color: rgba(255,255,255,0.25) !important;
}
</style>
"""


def scrub(html: str) -> tuple[str, int]:
    before = html
    html, n = LEAK_RE.subn("\n", html)
    # Also remove any leftover comment+function if regex missed due to formatting
    if "/* Virtus Core experience_language */" in html and "(function ()" in html:
        # Remove unwrapped blocks between style close and next script
        html2 = re.sub(
            r"(?ms)</style>\s*/\*\s*Virtus Core experience_language\s*\*/\s*\(function\s*\(\)\s*\{.*?\}\)\s*\(\)\s*;\s*(?=<script|\Z)",
            "</style>\n",
            html,
        )
        if html2 != html:
            n += 1
            html = html2
    if "vitrine-contrast-fix" not in html:
        if "</head>" in html:
            html = html.replace("</head>", CONTRAST_CSS + "\n</head>", 1)
        else:
            html = CONTRAST_CSS + html
    return html, n if html != before or "vitrine-contrast-fix" in html else n


def main() -> None:
    for niche in NICHES:
        path = PREVIEWS / "sites" / "premium" / niche / "index.html"
        text = path.read_text(encoding="utf-8")
        new, n = scrub(text)
        # verify no visible leak remains in body-ish text after last </style> before scripts
        if re.search(
            r"</style>\s*/\*\s*Virtus Core experience_language",
            new,
        ) or re.search(
            r"(?m)^\s*/\*\s*Virtus Core experience_language\s*\*/\s*\(function",
            new,
        ):
            # force remove every bare occurrence of the IIFE after experience_language comment outside script
            parts = new.split("/* Virtus Core experience_language */")
            rebuilt = [parts[0]]
            removed = 0
            for chunk in parts[1:]:
                # CSS block starts with :root — keep
                if chunk.lstrip().startswith(":root") or chunk.lstrip().startswith("\n:root"):
                    rebuilt.append("/* Virtus Core experience_language */" + chunk)
                    continue
                # JS IIFE — drop until ); following })();
                m = re.match(r"(?s)\s*\(function\s*\(\)\s*\{.*?\}\)\s*\(\)\s*;\s*", chunk)
                if m:
                    rebuilt.append(chunk[m.end() :])
                    removed += 1
                else:
                    rebuilt.append("/* Virtus Core experience_language */" + chunk)
            new = "".join(rebuilt)
            n += removed
        if "experience_language" in new and "(function ()" in new:
            # final safety: delete lines that are clearly the leaked IIFE marker outside script tags
            pass
        path.write_text(new, encoding="utf-8")
        leak_left = "prefers-reduced-motion" in Path(path).read_text(encoding="utf-8")
        # prefers-reduced-motion may still exist inside proper script elsewhere — check bare form
        raw = path.read_text(encoding="utf-8")
        bare = bool(
            re.search(
                r"(?m)^\s*/\*\s*Virtus Core experience_language\s*\*/\s*\n\s*\(function",
                raw,
            )
        )
        print(f"{niche}: removed_blocks~{n} bare_leak={bare}")


if __name__ == "__main__":
    main()
