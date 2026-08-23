"""Demo Gallery audit for CEO Dashboard — filesystem truth for package-previews."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MIN_FULL_BYTES = 5000
GALLERY_SCHEMA = "tier_v2"

# Carousel niches that must show honest Starter vs Premium (not recycled Business HTML).
TIER_COMPARE_NICHES = ("dental", "psychology", "auto", "beauty")
PREMIUM_GALLERY_NICHES = (
    "dental",
    "psychology",
    "auto",
    "beauty",
    "law",
    "restaurant",
    "realestate",
    "energy",
)

WEBSITE_REQUIRED = (
    "dental",
    "law",
    "restaurant",
    "beauty",
    "auto",
    "fitness",
    "handwerk",
    "it",
)
STORE_REQUIRED = (
    "fashion",
    "beauty",
    "electronics",
    "furniture",
    "food",
    "handwerk",
)


def _previews_root() -> Path:
    # .../dashboard/backend/app/integration → parents[3] = dashboard
    return Path(__file__).resolve().parents[3] / "frontend" / "public" / "package-previews"


def _probe(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "exists": False,
            "bytes": 0,
            "status": "missing",
        }
    size = path.stat().st_size
    status = "pass" if size >= MIN_FULL_BYTES else "thin"
    return {
        "exists": True,
        "bytes": size,
        "status": status,
        "mtime": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
    }


def _read_meta(dest: Path) -> dict[str, Any] | None:
    meta = dest / "demo_gallery_meta.json"
    if not meta.is_file():
        return None
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _html_tier(index: Path) -> str | None:
    if not index.is_file():
        return None
    try:
        # Prefer <body …> — CSS also contains body[data-tier="…"] rules for all tiers.
        head = index.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r"<body\b[^>]*\bdata-tier=[\"'](basic|business|premium)[\"']", head, re.I)
    return m.group(1).lower() if m else None


def audit_demo_freshness(root: Path | None = None) -> dict[str, Any]:
    """Demo Freshness Gate — gallery must use current Factory tiers, not recycled HTML.

    Fails when Basic/Premium folders still contain Business-tier HTML or lack meta.
    """
    root = root or _previews_root()
    issues: list[str] = []
    checks: list[dict[str, Any]] = []

    def check_demo(tier: str, niche: str, *, require_vie: bool) -> None:
        dest = root / "sites" / tier / niche
        index = dest / "index.html"
        meta = _read_meta(dest)
        html_tier = _html_tier(index)
        row: dict[str, Any] = {
            "tier": tier,
            "niche": niche,
            "exists": index.is_file(),
            "html_tier": html_tier,
            "meta_package_id": (meta or {}).get("package_id"),
            "gallery_schema": (meta or {}).get("gallery_schema"),
            "has_meta": meta is not None,
        }
        ok = True
        if not index.is_file():
            ok = False
            issues.append(f"missing {tier}/{niche}")
        elif html_tier != tier:
            ok = False
            issues.append(
                f"{tier}/{niche}: HTML data-tier={html_tier or 'missing'} (expected {tier}) — stale demo"
            )
        elif not meta:
            ok = False
            issues.append(f"{tier}/{niche}: missing demo_gallery_meta.json")
        elif meta.get("package_id") != tier:
            ok = False
            issues.append(f"{tier}/{niche}: meta package_id={meta.get('package_id')}")
        elif tier in ("basic", "premium") and meta.get("gallery_schema") != GALLERY_SCHEMA:
            ok = False
            issues.append(
                f"{tier}/{niche}: gallery_schema={meta.get('gallery_schema')} (want {GALLERY_SCHEMA})"
            )
        if require_vie and index.is_file():
            try:
                head = index.read_text(encoding="utf-8", errors="replace")
            except OSError:
                head = ""
            body_m = re.search(r"<body\b[^>]*>", head, re.I)
            body_tag = body_m.group(0) if body_m else ""
            if "data-vie-engine" not in body_tag and tier in ("business", "premium"):
                ok = False
                issues.append(f"{tier}/{niche}: missing data-vie-engine (old layout)")
            # Placeholder smell (body/content, not CSS comments)
            for bad in ("lorem ipsum", "placeholder.jpg", "TODO_HERO"):
                if bad.lower() in head.lower():
                    ok = False
                    issues.append(f"{tier}/{niche}: placeholder '{bad}'")
                    break
        row["ok"] = ok
        row["mark"] = "🟢" if ok else "🔴"
        checks.append(row)

    for niche in TIER_COMPARE_NICHES:
        check_demo("basic", niche, require_vie=False)
    for niche in WEBSITE_REQUIRED:
        check_demo("business", niche, require_vie=True)
    for niche in PREMIUM_GALLERY_NICHES:
        check_demo("premium", niche, require_vie=True)

    # Orphan "path" premium demo is not allowed as customer-facing sample
    path_demo = root / "sites" / "premium" / "path" / "index.html"
    if path_demo.is_file():
        issues.append("premium/path still present — replace with real niches")
        checks.append(
            {
                "tier": "premium",
                "niche": "path",
                "ok": False,
                "mark": "🔴",
                "exists": True,
                "note": "orphan stale demo",
            }
        )

    catalog = root / "GALLERY_INDEX.json"
    catalog_schema = None
    if catalog.is_file():
        try:
            catalog_schema = json.loads(catalog.read_text(encoding="utf-8")).get(
                "gallery_schema"
            )
        except (OSError, json.JSONDecodeError):
            catalog_schema = None
    # Soft: only fail catalog schema when basic/premium already claim tier_v2 but index does not.
    basic_has_v2 = any(
        c.get("tier") == "basic" and c.get("gallery_schema") == GALLERY_SCHEMA for c in checks
    )
    if basic_has_v2 and catalog_schema != GALLERY_SCHEMA:
        issues.append(f"GALLERY_INDEX gallery_schema={catalog_schema} (want {GALLERY_SCHEMA})")

    ok = not issues
    return {
        "id": "demo_freshness_gate",
        "title": "Demo Freshness Gate",
        "ok": ok,
        "status": "PASS" if ok else "FAIL",
        "mark": "🟢" if ok else "🔴",
        "schema": GALLERY_SCHEMA,
        "issues": issues[:40],
        "checks": checks,
        "ssot_ru": (
            "Demo Gallery должна показывать актуальные шаблоны Factory по пакетам "
            "Starter/Business/Premium. Старые Hero и чужой data-tier = FAIL релиза."
        ),
        "horizon_hook_ru": (
            "Позже: кнопка «▶ Смотреть рекламный ролик» → Horizon (Internal Only)."
        ),
    }


def build_demo_gallery_snapshot(memory_dir: Path | None = None) -> dict[str, Any]:
    """CEO card payload: Website 8/8 · AI Store 6/6 · Preview · Visual Quality · Freshness."""
    root = _previews_root()
    websites: list[dict[str, Any]] = []
    for niche in WEBSITE_REQUIRED:
        # Prefer business tier; beauty may live under basic historically
        candidates = [
            root / "sites" / "business" / niche / "index.html",
            root / "sites" / "basic" / niche / "index.html",
            root / "sites" / "premium" / niche / "index.html",
        ]
        hit = next((p for p in candidates if p.is_file()), candidates[0])
        row = _probe(hit)
        rel = (
            f"/package-previews/{hit.relative_to(root).as_posix()}"
            if hit.is_file()
            else f"/package-previews/sites/business/{niche}/index.html"
        )
        websites.append({"id": niche, "url": rel, **row})

    stores: list[dict[str, Any]] = []
    for sid in STORE_REQUIRED:
        path = root / "stores" / sid / "index.html"
        row = _probe(path)
        stores.append(
            {
                "id": sid,
                "url": f"/package-previews/stores/{sid}/index.html",
                **row,
            }
        )

    w_pass = sum(1 for w in websites if w["status"] == "pass")
    s_pass = sum(1 for s in stores if s["status"] == "pass")
    w_goal = len(WEBSITE_REQUIRED)
    s_goal = len(STORE_REQUIRED)

    # Preview PASS when CSP-capable files exist for primary carousel niches
    preview_ok = w_pass >= 4 and any(
        w["id"] == "dental" and w["status"] == "pass" for w in websites
    )

    # Byte-size heuristic (legacy CEO number) — NOT Visual Quality Gate PASS.
    total = w_goal + s_goal
    visual_bytes_score = round(100.0 * (w_pass + s_pass) / total) if total else 0

    # Visual Quality Gate (empty slots / placeholders) — separate from file size.
    try:
        from app.factory.visual_intelligence.business_visual_pack import (
            audit_demo_gallery_visual_quality,
        )

        vqg = audit_demo_gallery_visual_quality(root / "sites" / "business")
    except Exception as exc:
        vqg = {
            "ok": False,
            "status": "FAIL",
            "error": str(exc)[:160],
            "ssot": (
                "Business and Premium must not contain empty decorative zones. "
                "Every major visual slot must be filled."
            ),
        }

    freshness = audit_demo_freshness(root)

    last_gen = None
    catalog = root / "GALLERY_INDEX.json"
    if catalog.is_file():
        try:
            data = json.loads(catalog.read_text(encoding="utf-8"))
            last_gen = data.get("generated_at")
        except (OSError, json.JSONDecodeError):
            last_gen = None
    if not last_gen:
        mtimes = [
            r["mtime"]
            for r in websites + stores
            if r.get("mtime")
        ]
        last_gen = max(mtimes) if mtimes else None

    files_ok = w_pass == w_goal and s_pass == s_goal and preview_ok
    # Release gate: files + freshness (VQG already separate launch blocker)
    status = "PASS" if files_ok and freshness.get("ok") else "FAIL"
    if files_ok and not freshness.get("ok"):
        status = "STALE"

    return {
        "ok": True,
        "title": "Demo Gallery",
        "status": status,
        "websites": {"pass": w_pass, "goal": w_goal, "items": websites},
        "stores": {"pass": s_pass, "goal": s_goal, "items": stores},
        "preview": "PASS" if preview_ok else "FAIL",
        "visual_quality": visual_bytes_score,
        "visual_quality_gate": vqg,
        "demo_freshness_gate": freshness,
        "last_generated": last_gen,
        "paths_root": str(root),
        "tier_policy_ru": {
            "basic": "Starter 199 € — чистый современный дизайн, лёгкий motion",
            "business": "Business 399 € — Hero + KPI/trust, богаче motion",
            "premium": "Premium 699 € — premium_design, stats/showcase, cinematic heroes",
        },
    }
