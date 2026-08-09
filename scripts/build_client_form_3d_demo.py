"""Build website + store as if a German client filled the order form with 3D design.

Usage (from repo root):
  py -3.12 scripts/build_client_form_3d_demo.py

Outputs:
  dashboard/frontend/public/package-previews/client-forms/nordlicht-autohaus/
    website/index.html
    store/catalog.html
  OWNER_EYE_CHECKLIST.md (empty template for eye scores)
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
PUBLIC = ROOT / "dashboard" / "frontend" / "public" / "package-previews" / "client-forms"
OUT = PUBLIC / "nordlicht-autohaus"

sys.path.insert(0, str(BACKEND))


def _wipe(dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)


def main() -> int:
    os.environ.setdefault("VIRTUS_ALLOW_HTML_EXPORT", "1")

    from app.factory.factory_service import FactoryService
    from app.factory.motion_brief import gate_motion_level
    from app.factory.store_factory.composer import write_storefront
    from app.factory.store_factory.templates import StoreTemplateRegistry
    from app.factory.studio_renderer_v2 import decide_webgl, inject_studio_html, write_studio_assets
    from app.integration.shop_brief import validate_shop_brief

    # —— Formular (как заполнил владелец фирмы) ——
    form = {
        "business_name": "NordLicht Autohaus",
        "city": "München",
        "phone": "+49 89 1122334",
        "email": "kontakt@nordlicht-auto.example.de",
        "niche": "car_dealership",
        "package_id": "premium",
        "commerce_mode": "connected",
        "motion_level": "3d_premium",
        "brand_style": "luxury",
        "style": "luxury",
        "market_code": "DE",
        "ui_lang": "de",
        "language": "de",
        "services_list": [
            "Neuwagenberatung",
            "Gebrauchtwagen mit Historie",
            "Probefahrt",
            "Werkstatt & Inspektion",
            "Online-Zubehörshop",
        ],
        "advantages": [
            "Transparente Preise",
            "3D Showroom-Erlebnis",
            "Servicenetz München",
        ],
        "who_is_company": (
            "Familiengeführtes Autohaus in München — Auswahl mit Klarheit "
            "statt Druckverkauf. Showroom und Werkstatt unter einem Dach."
        ),
        "client_story": "Schlüsselübergabe — und alles ist klar dokumentiert.",
        "main_promise": "Das nächste Auto ohne Überraschungen.",
        "why_choose_us": "Ehrliche Beratung, saubere Historie, 3D-Showroom, Shop für Pflege.",
        "dream_wishes": "Website wie eine teure Münchner Digitalagentur + Online-Shop für Zubehör.",
        "keep_business_name": True,
        "demo_gallery": True,
        "diversity_salt": "client-form-3d-nordlicht-2026",
    }

    decision = decide_webgl(form["niche"], form["package_id"])
    gate = gate_motion_level(
        form["motion_level"],
        package_id=form["package_id"],
        niche_id=form["niche"],
    )
    print("FORM niche=", form["niche"], "package=", form["package_id"])
    print("WEBGL enabled=", decision.enabled, "mode=", decision.mode)
    print("SELL REASON=", decision.sell_reason)
    print("MOTION GATE=", gate)
    if not gate.get("ok"):
        print("FAIL: 3D form was waitlisted — abort")
        return 1

    sandbox = BACKEND / ".tmp_client_form_3d"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True)

    factory = FactoryService(memory_dir=sandbox, sandbox_dir=sandbox)
    description = (
        f"{form['business_name']} {form['city']} — {form['who_is_company']} "
        f"Wunsch: echtes 3D-Showroom-Erlebnis und Online-Shop für Autopflege."
    )
    summary = factory.build_landing(
        description,
        package_id="premium",
        contacts=form,
        market_code="DE",
        motion_level="3d_premium",
    )
    product_id = summary["product_id"]
    product_dir = sandbox / product_id
    print("WEBSITE product_id=", product_id)

    website_dest = OUT / "website"
    _wipe(website_dest)
    shutil.copytree(product_dir, website_dest, dirs_exist_ok=True)

    write_studio_assets(
        website_dest,
        niche_id="car_dealership",
        package_id="premium",
        business_name=form["business_name"],
        metaphor="Showroom key handover",
        accent_hex="#c5a572",
    )
    index = website_dest / "index.html"
    if index.is_file():
        html = inject_studio_html(index.read_text(encoding="utf-8"), package_id="premium")
        if 'id="virtus-3d-mount"' not in html and "lx-hero" in html:
            html = html.replace(
                '<header class="lx-hero"',
                '<div id="virtus-3d-mount" class="lx-hero-3d" style="position:absolute;inset:0;z-index:1;pointer-events:none;opacity:.9" aria-hidden="true"></div>\n  <header class="lx-hero"',
                1,
            )
        if "scene_3d.js" not in html:
            html = html.replace(
                "</body>",
                '<script src="assets/scene_3d.js" defer></script>\n</body>',
            )
        index.write_text(html, encoding="utf-8")

    # —— Store (same firm, Zubehör) ——
    store_dest = OUT / "store"
    _wipe(store_dest)
    brief = validate_shop_brief(
        {
            "company_name": form["business_name"],
            "store_name": "NordLicht Care Shop",
            "what_is_sold": (
                "Autopflege, Innenraumschutz, Felgenpflege, "
                "Winter-Sets und Zubehör mit DHL-Versand"
            ),
            "category": "auto_parts",
            "catalog_size": "24",
            "languages": ["de"],
            "currency": "EUR",
            "payments": ["stripe"],
            "shipping": ["dhl"],
            "pages": [
                "home",
                "catalog",
                "pdp",
                "about",
                "contact",
                "legal",
                "returns",
                "cart",
                "checkout",
                "account",
            ],
            "style": "luxury",
            "package_id": "premium",
            "market_code": "DE",
            "demo_gallery": True,
            "diversity_salt": "client-form-3d-nordlicht-shop",
        }
    )
    resolved = StoreTemplateRegistry().resolve(brief)
    write_storefront(store_dest, brief=brief, resolved=resolved)

    meta = {
        "form": form,
        "webgl": decision.as_dict(),
        "motion_gate": gate,
        "website_url": "/package-previews/client-forms/nordlicht-autohaus/website/",
        "store_url": "/package-previews/client-forms/nordlicht-autohaus/store/catalog.html",
        "product_id": product_id,
        "note": "NO COMMIT until Owner Eye checklist PASS",
    }
    (OUT / "CLIENT_FORM.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUT / "OWNER_EYE_CHECKLIST.md").write_text(
        """# Owner Eye — NordLicht Autohaus (Client Form 3D)

Do **not** commit until this is filled by eye.

## Website
- [ ] Hero full viewport
- [ ] WebGL works (not black square)
- [ ] Car reflection + light + motion
- [ ] Every section has its own image
- [ ] Gallery 10–12 **unique** photos (not repeats)
- [ ] No Hero repeat lower on page
- [ ] No Pillow illustrations
- [ ] No broken images
- [ ] Text readable on backgrounds

## Store
- [ ] Feels same brand as website
- [ ] Catalog loads
- [ ] Product photos look premium

## German studio test
> If I remove the Virtus Core logo, do I believe an expensive German digital studio made this?

Website: ___ / 10
Store: ___ / 10

Verdict: PASS / FAIL
""",
        encoding="utf-8",
    )

    print("OUT", OUT)
    print("website", website_dest / "index.html")
    print("store", store_dest / "catalog.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
