"""Audit public /site preview links: existence, media floor, uniqueness."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "dashboard" / "frontend" / "public"
HUB = ROOT / "dashboard" / "frontend" / "app" / "components" / "storefront" / "AppStoreHub.tsx"


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()[:12]


def check_site(rel: str) -> dict:
    base = PUBLIC / rel.lstrip("/").replace("\\", "/")
    # index.html or directory
    if rel.endswith("/"):
        index = PUBLIC / rel.strip("/") / "index.html"
    elif rel.endswith(".html"):
        index = PUBLIC / rel.lstrip("/")
    else:
        index = PUBLIC / rel.lstrip("/") / "index.html"
        if not index.is_file():
            index = PUBLIC / (rel.lstrip("/") + ".html")
    out = {
        "href": rel,
        "index": str(index.relative_to(PUBLIC)) if index.is_file() else None,
        "exists": index.is_file(),
        "hero": None,
        "hero_bytes": 0,
        "hero_hash": None,
        "issues": [],
    }
    if not index.is_file():
        out["issues"].append("missing_index")
        return out
    folder = index.parent
    assets = folder / "assets"
    hero = assets / "hero.jpg"
    gallery = assets / "gallery.jpg"
    # store path
    store_hero = folder / "assets" / "images" / "hero.jpg"
    if store_hero.is_file():
        hero = store_hero
    elif not hero.is_file() and gallery.is_file():
        hero = gallery
    if hero.is_file():
        out["hero"] = str(hero.relative_to(PUBLIC))
        out["hero_bytes"] = hero.stat().st_size
        out["hero_hash"] = md5(hero)
        if hero.stat().st_size < 8000:
            out["issues"].append("tiny_hero")
    else:
        out["issues"].append("missing_hero")
    # css url refs
    html = index.read_text(encoding="utf-8", errors="ignore")
    urls = re.findall(r'url\(["\']?([^"\')]+)["\']?\)', html)
    miss = 0
    for u in urls[:40]:
        if u.startswith(("http", "data:", "#", "linear", "radial")):
            continue
        cand = (folder / u).resolve() if not u.startswith("/") else PUBLIC / u.lstrip("/")
        try:
            if not cand.is_file():
                miss += 1
        except Exception:
            miss += 1
    if miss:
        out["issues"].append(f"css_url_miss:{miss}")
    # legacy markers
    low = html.lower()
    if "studio-lumia" in str(index).lower() or "client-forms" in str(index).lower():
        out["issues"].append("client_form_path")
    if "g-xxxxxxxxxx" in low:
        out["issues"].append("placeholder_gtag")
    return out


def main() -> None:
    text = HUB.read_text(encoding="utf-8")
    hrefs = sorted(set(re.findall(r'href:\s*"(/package-previews/[^"]+)"', text)))
    thumbs = sorted(set(re.findall(r'thumb:\s*"(/[^"]+)"', text)))
    # hardcoded tier compare
    for m in re.findall(r'href="(/package-previews/[^"]+)"', text):
        if m not in hrefs:
            hrefs.append(m)
    print("=== HREFS ===")
    rows = []
    hashes: dict[str, list[str]] = {}
    for h in hrefs:
        r = check_site(h)
        rows.append(r)
        print(r["href"], "OK" if r["exists"] and not r["issues"] else "ISSUE", r["issues"], r.get("hero_bytes"))
        if r.get("hero_hash"):
            hashes.setdefault(r["hero_hash"], []).append(h)
    print("=== THUMBS ===")
    for t in thumbs:
        p = PUBLIC / t.lstrip("/")
        print(("OK" if p.is_file() and p.stat().st_size >= 8000 else "MISS"), t, p.stat().st_size if p.is_file() else 0)
    print("=== HERO DUPES ACROSS DEMOS ===")
    print({k: v for k, v in hashes.items() if len(v) > 1} or "none")
    # dental tiers
    print("=== DENTAL TIERS ===")
    for tier in ("basic", "business", "premium"):
        r = check_site(f"/package-previews/sites/{tier}/dental/index.html")
        print(tier, r)


if __name__ == "__main__":
    main()
