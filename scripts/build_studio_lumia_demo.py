"""Build Studio LUMIA — Luxury Nail · Brow · Lash · Massage (UA founder in DE).

NOT Autohaus. Soft 3D glass. Matching beauty store (no Gift Set / Starter Pack).

  py -3.12 scripts/build_studio_lumia_demo.py
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
OUT = (
    ROOT
    / "dashboard"
    / "frontend"
    / "public"
    / "package-previews"
    / "client-forms"
    / "studio-lumia"
)
SRC_ASSETS = Path(r"C:/Users/hppav/.cursor/projects/d-Games-Genesis-AI-Engine/assets")

sys.path.insert(0, str(BACKEND))
os.environ.setdefault("VIRTUS_ALLOW_HTML_EXPORT", "1")

PHOTO_MAP = {
    "lumia-01-hero.png": ["hero.jpg", "gallery_1.jpg", "background.jpg"],
    "lumia-02-reception.png": ["gallery_2.jpg", "section_contact.jpg"],
    "lumia-03-manicure.png": ["gallery_3.jpg", "illustration_1.jpg"],
    "lumia-04-pedicure.png": ["gallery_4.jpg"],
    "lumia-05-brows.png": ["gallery_5.jpg", "before.jpg"],
    "lumia-06-lashes.png": ["gallery_6.jpg", "after.jpg"],
    "lumia-07-massage.png": ["gallery_7.jpg", "section_story.jpg"],
    "lumia-08-cosmetics.png": ["gallery_8.jpg", "equipment.jpg", "illustration.jpg"],
    "lumia-09-workplace.png": ["gallery_9.jpg", "section_process.jpg", "process.jpg"],
    "lumia-10-team.png": ["gallery_10.jpg", "team.jpg", "section_team.jpg"],
    "lumia-11-certificates.png": ["gallery_11.jpg"],
    "lumia-12-client.png": ["gallery_12.jpg"],
    "lumia-13-interior.png": ["gallery_13.jpg", "section_services.jpg"],
    "lumia-14-products.png": ["gallery_14.jpg", "illustration_2.jpg"],
    "lumia-15-process.png": ["gallery_15.jpg"],
    "lumia-16-beforeafter.png": ["gallery_16.jpg", "before_after.jpg"],
    "lumia-17-lounge.png": ["gallery_17.jpg", "illustration_3.jpg"],
    "lumia-18-detail.png": ["gallery_18.jpg", "gallery.jpg"],
}


def _wipe(dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)


def _wire_photos(assets: Path) -> list[str]:
    from PIL import Image

    assets.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for png, names in PHOTO_MAP.items():
        src = SRC_ASSETS / png
        if not src.exists():
            print("MISS", png)
            continue
        im = Image.open(src).convert("RGB")
        for name in names:
            out = assets / name
            im.save(out, "JPEG", quality=90, optimize=True)
            written.append(name)
    return written


def _patch_website_html(website: Path) -> None:
    import re

    from app.factory.scene_3d_engine import write_hero_3d_snippet, write_scene_assets
    from app.factory.studio_renderer_v2 import inject_studio_html, write_studio_assets

    write_studio_assets(
        website,
        niche_id="nail_studio",
        package_id="premium",
        business_name="Studio LUMIA",
        metaphor="Soft glass float — calm luxury beauty",
        accent_hex="#c45c7a",
    )
    write_scene_assets(website, "nail_studio", "#c45c7a", "Studio LUMIA")
    write_hero_3d_snippet(website, "nail_studio", "#c45c7a", "Studio LUMIA")

    index = website / "index.html"
    html = index.read_text(encoding="utf-8")
    html = inject_studio_html(html, package_id="premium")

    # Soft 3D mount inside hero
    html = re.sub(r'\s*<div id="virtus-3d-mount"[^>]*>\s*</div>', "", html)
    if 'id="virtus-3d-mount"' not in html:
        html = re.sub(
            r'(<header class="[^"]*hero[^"]*"[^>]*>|<section class="[^"]*hero[^"]*"[^>]*>)',
            r'\1\n    <div id="virtus-3d-mount" class="lx-hero-3d" data-virtus-3d="1" aria-hidden="true"></div>',
            html,
            count=1,
        )
    if "scene_3d.js" not in html:
        html = html.replace(
            "</body>",
            '<script src="assets/scene_3d.js" defer></script>\n</body>',
        )

    # Unique gallery band 1..18
    def band_sub(m: re.Match[str], counter: list[int]) -> str:
        counter[0] += 1
        n = ((counter[0] - 1) % 18) + 1
        return f"{m.group(1)}gallery_{n}{m.group(2)}"

    c1: list[int] = [0]
    html = re.sub(
        r"(class=\"rx-band-img\"[^>]*url\('assets/)gallery_\d+(\.jpg'\))",
        lambda m: band_sub(m, c1),
        html,
    )
    c2: list[int] = [0]
    html = re.sub(
        r"(class=\"rx-svc-media\"[^>]*url\('assets/)gallery_\d+(\.jpg'\))",
        lambda m: band_sub(m, c2),
        html,
    )
    html = re.sub(
        r"(class=\"rx-about-media\"[^>]*url\('assets/)hero(\.jpg'\))",
        r"\1section_story\2",
        html,
    )

    css = """
<style id="lumia-studio-experience">
:root{
  --lumia-rose:#c45c7a; --lumia-cream:#f7efe8; --lumia-plum:#2a1824;
  --acc:#c45c7a;
}
body[data-niche="nail_studio"], body[data-niche="beauty"]{
  --p:#c45c7a; --acc:#c45c7a; --pd:#2a1824;
}
.lx-hero, .hero, header.lx-hero{
  position:relative!important; min-height:100vh!important; isolation:isolate; overflow:hidden!important;
  background: #2a1824 !important;
}
#virtus-3d-mount{
  position:absolute!important; inset:0!important; z-index:1!important;
  height:100%!important; min-height:100vh!important; pointer-events:none!important; opacity:.85;
}
#virtus-3d-hero{height:100%!important;min-height:100%!important;border-radius:0!important}
.lx-hero-media, .hero-media{
  position:absolute!important; inset:0!important; z-index:0!important; opacity:.42!important;
}
.lx-band, .fi-arc, [data-fi-panel]{
  position:relative!important; z-index:3!important;
  background:linear-gradient(115deg,rgba(42,24,36,.55),rgba(42,24,36,.08))!important;
  background-color:transparent!important;
}
.studio-band--story{--studio-bg:url('assets/section_story.jpg')}
.studio-band--services{--studio-bg:url('assets/section_services.jpg')}
.studio-band--team{--studio-bg:url('assets/section_team.jpg')}
.studio-band--process{--studio-bg:url('assets/section_process.jpg')}
.studio-band--contact{--studio-bg:url('assets/section_contact.jpg')}
</style>
"""
    if "lumia-studio-experience" not in html:
        html = html.replace("</head>", css + "</head>", 1)
    index.write_text(html, encoding="utf-8")


def main() -> int:
    from app.factory.factory_service import FactoryService
    from app.factory.motion_brief import gate_motion_level
    from app.factory.store_factory.composer import write_storefront
    from app.factory.store_factory.templates import StoreTemplateRegistry
    from app.factory.studio_renderer_v2 import decide_webgl
    from app.integration.shop_brief import validate_shop_brief

    form = {
        "business_name": "Studio LUMIA",
        "city": "München",
        "phone": "+49 89 4455667",
        "email": "hello@studio-lumia.example.de",
        "niche": "nail_studio",
        "package_id": "premium",
        "commerce_mode": "connected",
        "motion_level": "3d_premium",
        "brand_style": "editorial",
        "style": "warm",
        "market_code": "DE",
        "ui_lang": "de",
        "language": "de",
        "services_list": [
            "Maniküre & Gel",
            "Pediküre",
            "Augenbrauen",
            "Wimpernverlängerung",
            "Entspannungsmassage",
        ],
        "advantages": [
            "Ukrainische Präzision",
            "Ruhiges Atelier in München",
            "Pflegeprodukte zum Mitnehmen",
        ],
        "who_is_company": (
            "Studio LUMIA — gegründet von Olena Melnyk aus der Ukraine. "
            "Luxury Nail, Brow, Lash & Massage Atelier in München: "
            "warme Ruhe statt Massenstudio."
        ),
        "client_story": "Wenn du gehst, fühlt sich deine Haut und deine Form wieder wie du an.",
        "main_promise": "Nägel, Brauen, Wimpern und Massage — in einem ruhigen Münchner Atelier.",
        "why_choose_us": "Präzise Handarbeit, softes Licht, Produkte die wir selbst nutzen.",
        "dream_wishes": (
            "Website wie ein teures Beauty-Editorial mit soft 3D glass motion "
            "und Shop für Öle, Seren und Profi-Kosmetik — kein Autohaus, kein Gift Set."
        ),
        "keep_business_name": True,
        "demo_gallery": True,
        "diversity_salt": "studio-lumia-ua-muenchen-2026",
        "founder_origin": "UA",
        "founder_name": "Olena Melnyk",
    }

    decision = decide_webgl("nail_studio", "premium")
    gate = gate_motion_level(
        "3d_premium", package_id="premium", niche_id="nail_studio"
    )
    print("WEBGL", decision.as_dict())
    print("GATE", gate)
    if not gate.get("ok"):
        print("FAIL motion gate")
        return 1

    sandbox = BACKEND / ".tmp_studio_lumia"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True)

    factory = FactoryService(memory_dir=sandbox, sandbox_dir=sandbox)
    description = (
        f"{form['business_name']} München — {form['who_is_company']} "
        "Premium digital experience: soft glass 3D, cinematic beauty photography, "
        "matching cosmetics store."
    )
    summary = factory.build_landing(
        description,
        package_id="premium",
        contacts=form,
        market_code="DE",
        motion_level="3d_premium",
    )
    product_dir = sandbox / summary["product_id"]
    print("WEBSITE", summary["product_id"])

    website = OUT / "website"
    _wipe(website)
    shutil.copytree(product_dir, website, dirs_exist_ok=True)
    photos = _wire_photos(website / "assets")
    print("PHOTOS", len(photos))
    _patch_website_html(website)

    # Matching beauty store — same brand
    store = OUT / "store"
    _wipe(store)
    brief = validate_shop_brief(
        {
            "company_name": "Studio LUMIA",
            "store_name": "LUMIA Care Shop",
            "what_is_sold": (
                "Nagelöle, Brauenpflege, Wimpernserum, Massageöle, "
                "Handcremes, Profi-Kosmetik und Atelier-Rituale"
            ),
            "category": "beauty",
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
            "style": "warm",
            "package_id": "premium",
            "market_code": "DE",
            "demo_gallery": True,
            "diversity_salt": "studio-lumia-care-shop-2026",
            "color_scheme": "#c45c7a",
        }
    )
    resolved = StoreTemplateRegistry().resolve(brief)
    write_storefront(store, brief=brief, resolved=resolved)
    # Reuse studio product photos in store media if assets folder exists
    store_assets = store / "assets"
    store_assets.mkdir(parents=True, exist_ok=True)
    for i, key in enumerate(
        [
            "lumia-14-products.png",
            "lumia-08-cosmetics.png",
            "lumia-18-detail.png",
            "lumia-03-manicure.png",
            "lumia-07-massage.png",
            "lumia-15-process.png",
        ],
        start=1,
    ):
        src = SRC_ASSETS / key
        if src.exists():
            from PIL import Image

            Image.open(src).convert("RGB").save(
                store_assets / f"product_{i}.jpg", "JPEG", quality=88
            )

    meta = {
        "brand": "Studio LUMIA",
        "founder": "Olena Melnyk (UA → München)",
        "niche": "Luxury Nail · Brow · Lash · Massage",
        "webgl": decision.as_dict(),
        "website": "/package-previews/client-forms/studio-lumia/website/",
        "store": "/package-previews/client-forms/studio-lumia/store/catalog.html",
        "forbidden": ["Autohaus", "Gift Set", "Starter Pack", "Safe Space"],
        "photos_wired": len(photos),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "CLIENT_FORM.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "OWNER_EYE.md").write_text(
        """# Owner Eye — Studio LUMIA

Open:
- website/
- store/catalog.html

Must feel like a different agency than Autohaus.
Soft glass 3D only. 18 unique beauty photos. Store = same brand care products.
""",
        encoding="utf-8",
    )
    print("OUT", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
