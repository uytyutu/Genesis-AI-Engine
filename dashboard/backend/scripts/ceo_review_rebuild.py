"""Rebuild CEO eye-review builds after Visual Polish R-cycle."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

from app.factory.business_interview import interview_from_payload, interview_to_contacts
from app.factory.factory_service import FactoryService
from app.factory.premium_site_qa import run_premium_site_qa
from app.factory.website_design_spec import read_website_design_spec

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".ceo_review_builds"


def _build(
    factory: FactoryService,
    *,
    niche: str,
    name: str,
    desc: str,
    services: list[str],
    free: str,
    email: str,
    phone: str,
) -> tuple[str, Path, dict, dict, dict]:
    iv = interview_from_payload(
        {
            "company_name": name,
            "city": "Berlin",
            "free_text": free,
            "top_services": services,
            "style": "warm" if niche == "restaurant" else "technological",
            "niche": niche,
        }
    )
    contacts = interview_to_contacts(
        iv,
        {
            "phone": phone,
            "email": email,
            "domain_status": "need_help",
            "opening_hours": "Mo–Fr 8–18" if niche == "auto" else "Di–So 12–23",
            "package_id": "business",
            "market_code": "DE",
            "client_delivery": True,
        },
    )
    product = factory.build_landing(
        desc,
        package_id="business",
        market_code="DE",
        client_legal={
            "owner_name": "X",
            "street": "S 1",
            "zip": "10115",
            "city": "Berlin",
            "email": email,
            "phone": phone,
        },
        contacts=contacts,
    )
    pid = product["product_id"]
    product_dir = factory._sandbox / pid  # noqa: SLF001 — CEO review script
    meta = json.loads((product_dir / "meta.json").read_text(encoding="utf-8"))
    spec = read_website_design_spec(product_dir) or {}
    html = (product_dir / "index.html").read_text(encoding="utf-8")
    qa = run_premium_site_qa(
        html=html,
        meta=meta,
        niche_id=niche,
        design_spec=spec,
        assets_dir=product_dir / "assets",
    )
    return pid, product_dir, meta, spec, qa


def main() -> None:
    if OUT.is_dir():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    sandbox = OUT / "sandbox"
    factory = FactoryService(memory_dir=OUT, sandbox_dir=sandbox)

    builds = [
        (
            "automotive",
            "auto",
            "Kfz Meisterbetrieb Schmidt",
            "Kfz Berlin Werkstatt Inspektion Bremsen Service.",
            ["Inspektion", "Bremsenservice", "Oelwechsel"],
            "Werkstatt fuer Inspektion, Bremsen, Oelwechsel.",
            "service@kfz-schmidt.de",
            "+49 30 9876543",
        ),
        (
            "restaurant",
            "restaurant",
            "Restaurant Alt Berlin",
            "Restaurant Berlin Speisekarte Reservierung Weinbar.",
            ["Mittagstisch", "Abendkarte"],
            "Regionale Kueche, saisonale Speisekarte, Reservierung.",
            "gast@alt-berlin.de",
            "+49 30 4455667",
        ),
    ]

    manifest: dict[str, dict] = {}
    for label, niche, name, desc, services, free, email, phone in builds:
        pid, product_dir, meta, spec, qa = _build(
            factory,
            niche=niche,
            name=name,
            desc=desc,
            services=services,
            free=free,
            email=email,
            phone=phone,
        )
        manifest[label] = {
            "product_id": pid,
            "html": str(product_dir / "index.html"),
            "premium_qa": meta.get("premium_qa_verdict"),
            "owner_approve_allowed": qa.get("owner_approve_allowed"),
            "industry_family": spec.get("industry_family"),
            "renderer_strategy": spec.get("renderer_strategy"),
            "section_plan": spec.get("section_plan"),
            "differentiator_auto_vs_rest": spec.get("business", {}).get("differentiator"),
        }

    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    shots = OUT / "screenshots"
    shots.mkdir(exist_ok=True)
    checks: dict[str, dict] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        for label, info in manifest.items():
            url = Path(info["html"]).resolve().as_uri()
            checks[label] = {}
            for vp_name, size in (
                ("desktop", {"width": 1280, "height": 800}),
                ("mobile", {"width": 390, "height": 844}),
            ):
                ctx = browser.new_context(viewport=size)
                page = ctx.new_page()
                page.goto(url, wait_until="load", timeout=30000)
                page.wait_for_timeout(600)
                page.screenshot(
                    path=str(shots / f"{label}_{vp_name}_hero.png"), full_page=False
                )
                if vp_name == "desktop":
                    page.evaluate("window.scrollTo(0, 900)")
                    page.wait_for_timeout(400)
                    page.screenshot(path=str(shots / f"{label}_mid.png"), full_page=False)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(400)
                    page.screenshot(
                        path=str(shots / f"{label}_contact.png"), full_page=False
                    )
                metrics = page.evaluate(
                    """() => {
                      const hero = document.querySelector('[data-split-hero="1"]');
                      const media = document.querySelector(
                        '.cr-hero-stage, .rt-hero-media, .rx-hero-media, .cr-hero-photo'
                      );
                      const r = media
                        ? media.getBoundingClientRect()
                        : (hero ? hero.getBoundingClientRect() : null);
                      return {
                        heroCols: hero ? getComputedStyle(hero).gridTemplateColumns : '',
                        mediaW: r ? Math.round(r.width) : 0,
                        mediaH: r ? Math.round(r.height) : 0,
                        vw: window.innerWidth,
                        hasDemo: document.body.innerText.includes('Demonstrativ'),
                        hasRepNav: document.body.innerHTML.includes('>Reputation</a>'),
                        hasNachweise: document.body.innerHTML.includes('Nachweise</a>'),
                        hasFuerAscii: document.body.innerText.includes('fuer'),
                        hasFuerUmlaut: document.body.innerText.includes('für'),
                        hasOelAscii: /\\bOel\\b/.test(document.body.innerText),
                        hasOelUmlaut: document.body.innerText.includes('Öl'),
                      };
                    }"""
                )
                checks[label][vp_name] = metrics
                ctx.close()
        browser.close()

    (OUT / "checks.json").write_text(
        json.dumps(checks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary_path = OUT / "summary.json"
    summary_path.write_text(
        json.dumps({"manifest": manifest, "checks": checks}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(f"CEO review rebuild OK -> {summary_path}")


if __name__ == "__main__":
    main()
