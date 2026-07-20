"""Self-check: package preview thumbs exist on disk and are public-path ready.

Run from repo root:
  py -3.12 scripts/verify_package_preview_assets.py

Fails if any carousel image is missing from
dashboard/frontend/public/package-previews/ (would 404 in production).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "dashboard" / "frontend" / "public" / "package-previews"

# Keep in sync with dashboard/frontend/app/lib/packagePreviewGallery.ts
REQUIRED = [
    "sites/basic/auto/assets/gallery.jpg",
    "sites/basic/dental/assets/gallery.jpg",
    "sites/basic/beauty/assets/gallery.jpg",
    "sites/business/auto/assets/gallery.jpg",
    "sites/business/dental/assets/gallery.jpg",
    "sites/business/praxis/assets/gallery.jpg",
    "sites/premium/auto/assets/gallery.jpg",
    "sites/premium/dental/assets/gallery.jpg",
    "sites/premium/path/assets/gallery.jpg",
]


def main() -> int:
    missing: list[str] = []
    too_big: list[str] = []
    ok: list[str] = []
    for rel in REQUIRED:
        path = PUBLIC / rel
        if not path.is_file():
            missing.append(rel)
            continue
        size = path.stat().st_size
        if size < 1000:
            missing.append(f"{rel} (too small: {size})")
            continue
        if size > 400_000:
            too_big.append(f"{rel} ({size} bytes)")
        ok.append(f"/package-previews/{rel} ({size} B)")

    print("Package preview assets")
    for line in ok:
        print(f"  OK  {line}")
    if missing:
        print("MISSING (would 404 in production):")
        for m in missing:
            print(f"  FAIL  {m}")
    if too_big:
        print("WARN oversized for mobile:")
        for t in too_big:
            print(f"  WARN  {t}")

    if missing:
        return 1
    print(f"PASS {len(ok)}/{len(REQUIRED)} thumbs ready for git + deploy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
