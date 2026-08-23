"""Pre-flight niche audit before vitrine sync."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / "scripts"))

from sync_public_package_previews import STORE_CASES, WEBSITE_CASES  # noqa: E402
from app.factory.store_factory.design_bridge import STORE_CATEGORY_TO_NICHE  # noqa: E402
from app.factory.store_factory.store_media import _repo_showcases  # noqa: E402


def main() -> int:
    sc = _repo_showcases()
    showcase_dirs = {p.name for p in sc.iterdir() if p.is_dir()} if sc.is_dir() else set()
    print("SHOWCASE_ROOT", sc, "exists", sc.is_dir())
    print("SHOWCASE_NICHES", sorted(showcase_dirs))
    print("WEBSITE_CASES", len(WEBSITE_CASES))
    print("STORE_CASES", len(STORE_CASES))

    web_folders = [c["folder"] for c in WEBSITE_CASES]
    store_folders = [c["folder"] for c in STORE_CASES]
    print("WEB_FOLDERS", web_folders)
    print("STORE_FOLDERS", store_folders)

    issues: list[str] = []
    for c in WEBSITE_CASES:
        niche = c["niche"]
        # map psychology etc to showcase folders
        mapped = niche
        if niche in ("gartenpflege", "zaunbau", "dachreinigung"):
            mapped = "green"
        if niche not in showcase_dirs and mapped not in showcase_dirs:
            # check hero files under niche or generic
            issues.append(f"website niche '{niche}' has no showcase dir (mapped={mapped})")

    for c in STORE_CASES:
        cat = c["category"]
        niche = STORE_CATEGORY_TO_NICHE.get(cat, cat)
        if niche not in showcase_dirs and "generic" not in showcase_dirs:
            issues.append(f"store {c['folder']} category={cat} niche={niche} missing showcase")
        # count jpgs
        root = sc / niche if (sc / niche).is_dir() else sc / "generic"
        jpgs = list(root.rglob("*.jpg")) + list(root.rglob("*.jpeg")) + list(root.rglob("*.webp"))
        if len(jpgs) == 0:
            issues.append(f"store {c['folder']} showcase '{root.name}' has 0 images")

    # existing public previews empty heroes?
    public = ROOT / "dashboard" / "frontend" / "public" / "package-previews"
    empty: list[str] = []
    if public.is_dir():
        for hero in public.rglob("hero.jpg"):
            if hero.stat().st_size < 4000:
                empty.append(f"{hero.relative_to(public)} size={hero.stat().st_size}")
        for hero in public.rglob("hero_1.jpg"):
            if hero.stat().st_size < 4000:
                empty.append(f"{hero.relative_to(public)} size={hero.stat().st_size}")

    report = {
        "website_count": len(WEBSITE_CASES),
        "store_count": len(STORE_CASES),
        "issues": issues,
        "empty_or_tiny_public_heroes": empty[:40],
        "empty_count": len(empty),
    }
    out = ROOT / "_tmp_niche_audit.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
