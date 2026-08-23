"""Rebuild GALLERY_INDEX.json from filesystem (premium + existing tiers)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "dashboard" / "frontend" / "public" / "package-previews"
sys.path.insert(0, str(ROOT / "scripts"))

from sync_public_package_previews import write_catalog  # noqa: E402

MIN_FULL = 5000


def scan() -> list[dict]:
    rows: list[dict] = []
    for tier_dir in (PUBLIC / "sites").iterdir() if (PUBLIC / "sites").is_dir() else []:
        if not tier_dir.is_dir():
            continue
        tier = tier_dir.name
        for niche in sorted(tier_dir.iterdir()):
            if not niche.is_dir():
                continue
            idx = niche / "index.html"
            if not idx.is_file():
                continue
            size = idx.stat().st_size
            status = "PASS" if size >= MIN_FULL else "THIN"
            rows.append(
                {
                    "kind": "website",
                    "id": niche.name,
                    "package_id": tier,
                    "status": status,
                    "bytes": size,
                    "url": f"/package-previews/sites/{tier}/{niche.name}/index.html",
                }
            )
    stores_root = PUBLIC / "stores"
    if stores_root.is_dir():
        for child in sorted(stores_root.iterdir()):
            if not child.is_dir():
                continue
            # tiered stores/<tier>/<folder> or legacy stores/<folder>
            if (child / "catalog.html").is_file() or (child / "index.html").is_file():
                page = child / "catalog.html" if (child / "catalog.html").is_file() else child / "index.html"
                size = page.stat().st_size
                rows.append(
                    {
                        "kind": "store",
                        "id": child.name,
                        "package_id": "business",
                        "status": "PASS" if size >= MIN_FULL else "THIN",
                        "bytes": size,
                        "url": f"/package-previews/stores/{child.name}/catalog.html"
                        if page.name == "catalog.html"
                        else f"/package-previews/stores/{child.name}/index.html",
                    }
                )
                continue
            tier = child.name
            for folder in sorted(child.iterdir()):
                if not folder.is_dir():
                    continue
                page = (
                    folder / "catalog.html"
                    if (folder / "catalog.html").is_file()
                    else folder / "index.html"
                )
                if not page.is_file():
                    continue
                size = page.stat().st_size
                rows.append(
                    {
                        "kind": "store",
                        "id": f"{tier}/{folder.name}",
                        "package_id": tier,
                        "status": "PASS" if size >= MIN_FULL else "THIN",
                        "bytes": size,
                        "url": (
                            f"/package-previews/stores/{tier}/{folder.name}/catalog.html"
                            if page.name == "catalog.html"
                            else f"/package-previews/stores/{tier}/{folder.name}/index.html"
                        ),
                    }
                )
    return rows


def main() -> int:
    rows = scan()
    write_catalog(rows)
    print(f"rebuilt {len(rows)} items @ {datetime.now(timezone.utc).isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
