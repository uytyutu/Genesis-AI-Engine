"""Export CEO product-package demos: Autowerkstatt, Praxis, Beauty + 3 client paths.

Run from repo root or dashboard/backend:
  py -3.12 dashboard/backend/scripts/export_package_product_demos.py

Writes under dashboard/backend/.factory_ceo_package_previews/
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from app.factory.factory_service import FactoryService

OUT = Path(__file__).resolve().parents[1] / ".factory_ceo_package_previews"
SANDBOX = OUT / "_product_build"

# Package demos: niche x tier
PACKAGE_DEMOS: list[dict] = [
    {
        "slug": "auto_basic",
        "package_id": "basic",
        "description": "Autowerkstatt Bergmann — Inspektion, Diagnose und Reifen in Köln",
        "contacts": {
            "business_name": "Autowerkstatt Bergmann",
            "phone": "+49 221 555 0100",
            "whatsapp": "+49 171 5550100",
            "email": "info@auto-demo.de",
            "city": "Köln",
            "street": "Rheinstraße 12",
        },
    },
    {
        "slug": "auto_business",
        "package_id": "business",
        "description": "Autowerkstatt Bergmann — Inspektion, Diagnose und Reifen in Köln",
        "contacts": {
            "business_name": "Autowerkstatt Bergmann",
            "phone": "+49 221 555 0100",
            "whatsapp": "+49 171 5550100",
            "email": "info@auto-demo.de",
            "city": "Köln",
            "street": "Rheinstraße 12",
        },
    },
    {
        "slug": "auto_premium",
        "package_id": "premium",
        "description": "Autowerkstatt Bergmann — Inspektion, Diagnose und Reifen in Köln",
        "contacts": {
            "business_name": "Autowerkstatt Bergmann",
            "phone": "+49 221 555 0100",
            "whatsapp": "+49 171 5550100",
            "email": "info@auto-demo.de",
            "city": "Köln",
            "street": "Rheinstraße 12",
        },
    },
    {
        "slug": "praxis_basic",
        "package_id": "basic",
        "description": "Arztpraxis Weber — Hausarztpraxis mit Prophylaxe und Impfungen in München",
        "contacts": {
            "business_name": "Arztpraxis Weber",
            "phone": "+49 89 555 0200",
            "whatsapp": "+49 171 5550200",
            "email": "kontakt@praxis-weber.de",
            "city": "München",
            "street": "Leopoldstraße 40",
        },
    },
    {
        "slug": "praxis_business",
        "package_id": "business",
        "description": "Arztpraxis Weber — Hausarztpraxis mit Prophylaxe und Impfungen in München",
        "contacts": {
            "business_name": "Arztpraxis Weber",
            "phone": "+49 89 555 0200",
            "whatsapp": "+49 171 5550200",
            "email": "kontakt@praxis-weber.de",
            "city": "München",
            "street": "Leopoldstraße 40",
        },
    },
    {
        "slug": "praxis_premium",
        "package_id": "premium",
        "description": "Arztpraxis Weber — Hausarztpraxis mit Prophylaxe und Impfungen in München",
        "contacts": {
            "business_name": "Arztpraxis Weber",
            "phone": "+49 89 555 0200",
            "whatsapp": "+49 171 5550200",
            "email": "kontakt@praxis-weber.de",
            "city": "München",
            "street": "Leopoldstraße 40",
        },
    },
]

# Three buyer paths (simple → mid → large)
CLIENT_PATHS: list[dict] = [
    {
        "slug": "path_beauty_basic",
        "label": "Клиент 1 · Basic · Ресницы",
        "package_id": "basic",
        "price": "350 €",
        "description": (
            "Lash Studio Mira — Wimpernverlängerung, Volumen und Brow Lamination in Hamburg. "
            "Beauty Studio für natürliche Looks."
        ),
        "contacts": {
            "business_name": "Lash Studio Mira",
            "phone": "+49 40 555 0300",
            "whatsapp": "+49 171 5550300",
            "email": "hello@lash-mira.de",
            "city": "Hamburg",
            "street": "Schanzenstraße 8",
        },
    },
    {
        "slug": "path_praxis_business",
        "label": "Клиент 2 · Business · Врач / Praxis",
        "package_id": "business",
        "price": "650 €",
        "description": (
            "Arztpraxis Dr. Keller — Hausarztpraxis mit Vorsorge, Impfungen und "
            "Online-Terminen in Berlin."
        ),
        "contacts": {
            "business_name": "Arztpraxis Dr. Keller",
            "phone": "+49 30 555 0400",
            "whatsapp": "+49 171 5550400",
            "email": "info@praxis-keller.de",
            "city": "Berlin",
            "street": "Friedrichstraße 100",
        },
    },
    {
        "slug": "path_auto_premium",
        "label": "Клиент 3 · Premium · Крупный авторемонт",
        "package_id": "premium",
        "price": "1 200 €",
        "description": (
            "NordAuto Service Gruppe — große Autowerkstatt und Flottenservice, "
            "Diagnose, Karosserie und Garantiearbeiten in Düsseldorf."
        ),
        "contacts": {
            "business_name": "NordAuto Service Gruppe",
            "phone": "+49 211 555 0500",
            "whatsapp": "+49 171 5550500",
            "email": "service@nordauto-gruppe.de",
            "city": "Düsseldorf",
            "street": "Rather Straße 200",
        },
    },
]


def _zip_dir(src: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(src).as_posix())


def _export_one(factory: FactoryService, spec: dict) -> dict:
    slug = spec["slug"]
    product = factory.build_landing(
        spec["description"],
        package_id=spec["package_id"],
        market_code="DE",
        contacts=spec["contacts"],
    )
    product_id = product["product_id"]
    src = SANDBOX / product_id
    dest = OUT / f"{slug}_site"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    # Flat single-file peek (index only) for quick open
    peek = OUT / f"{slug}.html"
    peek.write_text((dest / "index.html").read_text(encoding="utf-8"), encoding="utf-8")
    zip_path = OUT / f"{slug}.zip"
    _zip_dir(dest, zip_path)
    html = (dest / "index.html").read_text(encoding="utf-8")
    return {
        "slug": slug,
        "package_id": spec["package_id"],
        "label": spec.get("label") or slug,
        "price": spec.get("price") or "",
        "business": spec["contacts"]["business_name"],
        "site": f"{slug}_site/index.html",
        "zip": f"{slug}.zip",
        "has_process": 'id="process"' in html,
        "has_faq": 'id="faq"' in html,
        "has_maps": 'id="maps"' in html,
        "has_stats": 'id="stats"' in html,
        "has_catalog": 'id="catalog"' in html,
        "tier": f'data-tier="{spec["package_id"]}"' in html,
    }


def _write_gallery(rows: list[dict], path_rows: list[dict]) -> None:
    def links(items: list[dict]) -> str:
        bits = []
        for r in items:
            bits.append(
                f"<li><strong>{r['label'] or r['slug']}</strong> "
                f"({r['package_id']}{(' · ' + r['price']) if r['price'] else ''}) — "
                f"{r['business']}<br>"
                f"<a href=\"{r['site']}\">preview</a> · "
                f"<a href=\"{r['zip']}\">ZIP</a> · "
                f"process={'✅' if r['has_process'] else '—'} "
                f"faq={'✅' if r['has_faq'] else '—'} "
                f"maps={'✅' if r['has_maps'] else '—'} "
                f"stats={'✅' if r['has_stats'] else '—'}"
                f"</li>"
            )
        return "\n".join(bits)

    html = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Virtus Core — Product packages</title>
<style>
body{{font-family:system-ui;max-width:720px;margin:2rem auto;padding:0 1rem;line-height:1.55;color:#0f172a}}
h1{{font-size:1.6rem}} h2{{margin-top:2rem;font-size:1.2rem}}
li{{margin:1rem 0}} a{{color:#0369a1}} .note{{color:#64748b;font-size:.92rem}}
</style></head><body>
<h1>Product packages — витрина товара</h1>
<p class="note">Basic = готовый лендинг (process + mid-CTA + trust), без каркаса. Business = карта/FAQ/logo. Premium = stats/showcase/analytics. Каталог товаров на Path A отключён.</p>
<h2>Autowerkstatt · Praxis (Basic / Business / Premium)</h2>
<ul>{links(rows)}</ul>
<h2>Путь клиента (3 сценария)</h2>
<ul>{links(path_rows)}</ul>
</body></html>
"""
    (OUT / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if SANDBOX.exists():
        shutil.rmtree(SANDBOX)
    factory = FactoryService(memory_dir=SANDBOX, sandbox_dir=SANDBOX)
    package_rows = [_export_one(factory, s) for s in PACKAGE_DEMOS]
    path_rows = [_export_one(factory, s) for s in CLIENT_PATHS]
    _write_gallery(package_rows, path_rows)
    print(f"OK wrote {OUT}")
    for r in package_rows + path_rows:
        print(
            f"  {r['slug']:22} tier={r['package_id']:8} "
            f"process={r['has_process']} faq={r['has_faq']} "
            f"maps={r['has_maps']} stats={r['has_stats']} "
            f"catalog={r.get('has_catalog')}"
        )


if __name__ == "__main__":
    main()
