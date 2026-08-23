"""CEO Visual Review — human-gate companion (filesystem truth).

After every Demo Gallery rebuild, this gate checks the mandatory set:

  Starter / Business / Premium Dental
  Starter / Business / Premium Store (fashion)

FAIL if any looks like a stale template (wrong tier, thin HTML, empty UX,
missing Luxury markers on Premium, missing store chrome).

Does not replace human eyes — it blocks release when files are clearly wrong.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.integration.commercial_acceptance_gate import audit_ux_quality_html
from app.integration.demo_gallery_audit import _previews_root

ENGINE_ID = "ceo_visual_review_v1"
MIN_BYTES = 5000

# Mandatory CEO view set (paths relative to package-previews)
CEO_WEBSITES = (
    ("basic", "dental"),
    ("business", "dental"),
    ("premium", "dental"),
)
CEO_STORES = (
    ("basic", "fashion"),
    ("business", "fashion"),
    ("premium", "fashion"),
)

KPI_RU = "Купил бы я здесь товар? / Показал бы первому клиенту без стыда?"


def _body_attr(html: str, name: str) -> str | None:
    m = re.search(rf"<body\b[^>]*\b{name}=[\"']([^\"']+)[\"']", html, re.I)
    return m.group(1) if m else None


def _review_site(path: Path, *, expect_tier: str) -> dict[str, Any]:
    label = f"sites/{expect_tier}/dental"
    if not path.is_file():
        return {
            "id": label,
            "ok": False,
            "status": "FAIL",
            "issues": [f"{label}: missing index.html"],
        }
    size = path.stat().st_size
    html = path.read_text(encoding="utf-8", errors="replace")
    issues: list[str] = []
    if size < MIN_BYTES:
        issues.append(f"{label}: thin HTML ({size}B)")
    tier = _body_attr(html, "data-tier")
    if tier != expect_tier:
        issues.append(f"{label}: data-tier={tier!r} expected {expect_tier!r}")
    if expect_tier == "premium":
        lux = _body_attr(html, "data-luxury")
        if lux != "1":
            issues.append(f"{label}: Premium without data-luxury=1 (stale gallery?)")
        if "digital-creative-studio" not in html and "data-studio" not in html.lower():
            issues.append(f"{label}: missing studio markers")
    ux = audit_ux_quality_html(html, label=label)
    issues.extend(ux.get("issues") or [])
    ok = not issues
    return {
        "id": label,
        "ok": ok,
        "status": "PASS" if ok else "FAIL",
        "bytes": size,
        "tier": tier,
        "luxury": _body_attr(html, "data-luxury"),
        "issues": issues[:20],
        "url": f"/package-previews/sites/{expect_tier}/dental/index.html",
    }


def _review_store(path: Path, *, expect_tier: str, folder: str = "fashion") -> dict[str, Any]:
    label = f"stores/{expect_tier}/{folder}"
    if not path.is_file():
        # Legacy flat path fallback for business
        legacy = _previews_root() / "stores" / folder / "index.html"
        if expect_tier == "business" and legacy.is_file():
            path = legacy
            label = f"stores/{folder} (legacy)"
        else:
            return {
                "id": label,
                "ok": False,
                "status": "FAIL",
                "issues": [f"{label}: missing index.html — rebuild with visual_reality_rebuild"],
            }
    size = path.stat().st_size
    html = path.read_text(encoding="utf-8", errors="replace")
    issues: list[str] = []
    if size < MIN_BYTES:
        issues.append(f"{label}: thin HTML ({size}B)")
    low = html.lower()
    store_dir = path.parent
    for need, msg in (
        ("header-search", "search"),
        ("account.html", "Login/Register / account"),
        ("cart.html", "cart"),
        ("product-card", "product cards"),
    ):
        if need not in low:
            issues.append(f"{label}: missing {msg}")
    if not (store_dir / "checkout.html").is_file() and "checkout.html" not in low:
        issues.append(f"{label}: missing checkout")
    # Commercial Store KPI: photos required (letter placeholders = FAIL)
    img_count = len(re.findall(r"<img\b", html, flags=re.I))
    if img_count < 3:
        issues.append(f"{label}: too few <img> ({img_count}) — store needs product/hero photos")
    hero_img = (store_dir / "assets" / "images" / "hero.jpg").is_file()
    if not hero_img:
        issues.append(f"{label}: missing assets/images/hero.jpg")
    product_imgs = list((store_dir / "assets" / "images").glob("product*.jpg")) if (store_dir / "assets" / "images").is_dir() else []
    if len(product_imgs) < 2:
        issues.append(f"{label}: need product photos (found {len(product_imgs)})")
    if expect_tier == "premium":
        if "data-studio" not in low and "digital-creative-studio" not in low:
            issues.append(f"{label}: Premium Store missing studio markers")
        if "recommendations" not in low and "empfehlung" not in low:
            issues.append(f"{label}: no recommendations block")
        if "has-hero-image" not in low and "hero-photo" not in low:
            issues.append(f"{label}: Premium Store hero without photo")
    ux = audit_ux_quality_html(html, label=label)
    issues.extend(ux.get("issues") or [])
    ok = not issues
    return {
        "id": label,
        "ok": ok,
        "status": "PASS" if ok else "FAIL",
        "bytes": size,
        "issues": issues[:20],
        "url": f"/package-previews/{'stores/' + expect_tier + '/' + folder if 'legacy' not in label else 'stores/' + folder}/index.html",
    }


def run_ceo_visual_review(root: Path | None = None) -> dict[str, Any]:
    root = root or _previews_root()
    samples: list[dict[str, Any]] = []
    for tier, niche in CEO_WEBSITES:
        samples.append(
            _review_site(root / "sites" / tier / niche / "index.html", expect_tier=tier)
        )
    for tier, folder in CEO_STORES:
        samples.append(
            _review_store(
                root / "stores" / tier / folder / "index.html",
                expect_tier=tier,
                folder=folder,
            )
        )

    ok = all(s.get("ok") for s in samples)
    fails = [s for s in samples if not s.get("ok")]
    return {
        "engine": ENGINE_ID,
        "id": "ceo_visual_review",
        "title": "CEO Visual Review",
        "kpi_ru": KPI_RU,
        "ok": ok,
        "status": "PASS" if ok else "FAIL",
        "mark": "🟢" if ok else "🔴",
        "samples": samples,
        "fail_count": len(fails),
        "action_ru": (
            "PASS — файлы готовы к человеческому просмотру. Откройте URL и ответьте на KPI."
            if ok
            else "FAIL — релиз заблокирован. Пересоберите Demo Gallery (visual_reality_rebuild)."
        ),
        "human_checklist_ru": [
            "За 5 секунд видно Starter < Business < Premium?",
            "Premium: показал бы первому клиенту без стыда?",
            "Store: доверил бы продавать товары?",
            "Нет пустых блоков / placeholder?",
            "Ощущение студии, не шаблона?",
        ],
        "ssot_ru": (
            "Любое изменение Visual Studio → автопересборка Demo Gallery → "
            "CEO Visual Review → только потом глазами. "
            "Главный KPI: показал бы я это первому клиенту без стыда?"
        ),
    }
