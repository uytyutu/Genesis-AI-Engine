"""Wire Cursor-generated unique photos into NordLicht client-form demo."""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image

SRC = Path(r"C:/Users/hppav/.cursor/projects/d-Games-Genesis-AI-Engine/assets")
ROOT = Path(
    r"D:/Games/Genesis-AI-Engine/dashboard/frontend/public/package-previews/"
    r"client-forms/nordlicht-autohaus/website"
)
DST = ROOT / "assets"

MAPPING = {
    "nordlicht-hero.png": ["hero.jpg", "gallery_1.jpg", "background.jpg"],
    "nordlicht-g02.png": ["gallery_2.jpg"],
    "nordlicht-g03.png": ["gallery_3.jpg", "before.jpg"],
    "nordlicht-g04.png": ["gallery_4.jpg", "section_process.jpg", "process.jpg", "after.jpg"],
    "nordlicht-g05.png": ["gallery_5.jpg", "equipment.jpg", "illustration_1.jpg"],
    "nordlicht-g06.png": ["gallery_6.jpg", "illustration_2.jpg"],
    "nordlicht-g07.png": ["gallery_7.jpg", "section_contact.jpg"],
    "nordlicht-g08.png": ["gallery_8.jpg", "illustration_3.jpg"],
    "nordlicht-g09.png": ["gallery_9.jpg", "illustration.jpg"],
    "nordlicht-g10.png": ["gallery_10.jpg", "gallery.jpg"],
    "nordlicht-g11.png": ["gallery_11.jpg", "team.jpg", "section_team.jpg"],
    "nordlicht-g12.png": ["gallery_12.jpg", "section_services.jpg"],
    "nordlicht-section-story.png": ["section_story.jpg", "before_after.jpg"],
}


def main() -> None:
    for png, names in MAPPING.items():
        p = SRC / png
        if not p.exists():
            print("MISS", png)
            continue
        im = Image.open(p).convert("RGB")
        for n in names:
            im.save(DST / n, "JPEG", quality=88, optimize=True)
            print("wrote", n, (DST / n).stat().st_size)

    html_path = ROOT / "index.html"
    html = html_path.read_text(encoding="utf-8")

    html = html.replace(
        "url('assets/hero.jpg')\"></div>\n      <p class=\"rx-hero-eyebrow\"",
        "url('assets/hero.jpg')\"></div>\n      <p class=\"rx-hero-eyebrow\"",
    )

    html = html.replace(
        "url('assets/hero.jpg')\"></div>\n    <div class=\"rx-about-copy\"",
        "url('assets/section_story.jpg')\"></div>\n    <div class=\"rx-about-copy\"",
    )
    # about media variants
    html = re.sub(
        r"(class=\"rx-about-media\"[^>]*url\('assets/)hero(\.jpg'\))",
        r"\1section_story\2",
        html,
    )

    svc_i = 0

    def svc_sub(m: re.Match[str]) -> str:
        nonlocal svc_i
        svc_i += 1
        n = ((svc_i - 1) % 12) + 1
        return f"{m.group(1)}gallery_{n}{m.group(2)}"

    html = re.sub(
        r"(class=\"rx-svc-media\"[^>]*url\('assets/)gallery_[123](\.jpg'\))",
        svc_sub,
        html,
    )

    band_i = 0

    def band_sub(m: re.Match[str]) -> str:
        nonlocal band_i
        band_i += 1
        n = ((band_i - 1) % 12) + 1
        return f"{m.group(1)}gallery_{n}{m.group(2)}"

    html = re.sub(
        r"(class=\"rx-band-img\"[^>]*url\('assets/)gallery_[123](\.jpg'\))",
        band_sub,
        html,
    )

    # Force CSS section backgrounds off repeated hero where studio-band handles plates
    html = html.replace(
        'url("assets/hero.jpg") !important;',
        'url("assets/section_story.jpg") !important;',
    )
    # Keep cinematic hero CSS for .lx-hero / .hero
    html = re.sub(
        r"(\.lx-hero[^{]*\{[^}]*url\(\"assets/)section_story(\.jpg\")",
        r"\1hero\2",
        html,
        count=2,
    )

    html_path.write_text(html, encoding="utf-8")
    sizes = {f"gallery_{i}.jpg": (DST / f"gallery_{i}.jpg").stat().st_size for i in range(1, 13)}
    print("sizes", sizes)
    print("small", [k for k, v in sizes.items() if v < 80000])
    print("svc", svc_i, "band", band_i, "hero_refs", html.count("assets/hero.jpg"))


if __name__ == "__main__":
    main()
