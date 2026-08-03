"""Generate Factory Golden Demo Set — regression baselines before Meta Ads.

Writes:
  dashboard/backend/app/factory/golden_demos/<niche>/
    questionnaire.json
    meta.json
    index.html
    impressum.html / datenschutz.html (if present)
    delivery.zip
    MANIFEST.json

Run from repo root:
  py -3.12 scripts/generate_factory_golden_demos.py
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from app.factory.factory_service import FactoryService  # noqa: E402

OUT = BACKEND / "app" / "factory" / "golden_demos"

# CEO Golden Demo Set — five commercial baselines
CASES = [
    {
        "niche": "dental",
        "business_name": "SmileCare Praxis",
        "city": "München",
        "description": (
            "SmileCare Praxis München — Zahnarztpraxis, Prophylaxe, Implantate, "
            "Ästhetik, schmerzarme Behandlung"
        ),
        "services_list": ["Prophylaxe", "Implantate", "Bleaching", "Füllungen"],
        "phone": "+49 89 1234567",
        "email": "kontakt@smilecare-golden.example.de",
        "advantages": ["Schmerzarme Behandlung", "Klare Kostenpläne", "Moderne Praxis"],
    },
    {
        "niche": "beauty",
        "business_name": "Salon Mira",
        "city": "Berlin",
        "description": (
            "Salon Mira Berlin — Friseursalon, Haarschnitt, Coloration, Balayage, Pflege"
        ),
        "services_list": ["Balayage", "Damenhaarschnitt", "Pflege", "Styling"],
        "phone": "+49 30 9876543",
        "email": "kontakt@salonmira-golden.example.de",
        "advantages": ["Online-Termine", "Premium-Produkte", "Erfahrene Stylisten"],
    },
    {
        "niche": "auto",
        "business_name": "Autowerkstatt Nord",
        "city": "Hamburg",
        "description": (
            "Autowerkstatt Nord Hamburg — Autowerkstatt, Diagnose, Inspektion, "
            "Reifen, Ölwechsel"
        ),
        "services_list": ["Diagnose", "Inspektion", "Reifen", "Ölwechsel"],
        "phone": "+49 40 5551212",
        "email": "kontakt@autownord-golden.example.de",
        "advantages": ["Schriftliche Diagnose", "Keine versteckten Posten", "Garantie"],
    },
    {
        "niche": "restaurant",
        "business_name": "Trattoria Luna",
        "city": "Köln",
        "description": (
            "Trattoria Luna Köln — Restaurant, Mittagstisch, Abendkarte, "
            "Reservierung, Events"
        ),
        "services_list": ["Mittagstisch", "Abendkarte", "Reservierung", "Events"],
        "phone": "+49 221 4445566",
        "email": "kontakt@trattorialuna-golden.example.de",
        "advantages": ["Frische Zutaten", "Reservierung mit Bestätigung", "Allergene klar"],
    },
    {
        "niche": "law",
        "business_name": "Kanzlei Weber",
        "city": "Frankfurt",
        "description": (
            "Kanzlei Weber Frankfurt — Rechtsanwalt, Wirtschaftsrecht, "
            "Vertragsprüfung, Erstberatung"
        ),
        "services_list": ["Erstberatung", "Vertragsprüfung", "Vertretung", "Verhandlungen"],
        "phone": "+49 69 7778899",
        "email": "kontakt@kanzleiweber-golden.example.de",
        "advantages": ["Vertraulich", "Klare Honorare", "Feste Ansprechpartner"],
    },
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    sandbox = OUT / "_sandbox_build"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True)

    factory = FactoryService(sandbox_dir=sandbox)
    catalog: list[dict] = []

    for case in CASES:
        niche = case["niche"]
        dest = OUT / niche
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)

        questionnaire = {
            "golden": True,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "package_id": "basic",
            "market_code": "DE",
            "language": "de",
            **case,
        }
        (dest / "questionnaire.json").write_text(
            json.dumps(questionnaire, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        contacts = {
            "business_name": case["business_name"],
            "city": case["city"],
            "phone": case["phone"],
            "email": case["email"],
            "whatsapp": case["phone"],
            "niche": niche,
            "services_list": case["services_list"],
            "advantages": case["advantages"],
            "package_id": "basic",
            "market_code": "DE",
            "ui_lang": "de",
            "language": "de",
            "brand_style": "auto",
        }
        summary = factory.build_landing(
            case["description"],
            package_id="basic",
            contacts=contacts,
            market_code="DE",
            motion_level="none",
        )
        product_id = summary["product_id"]
        product_dir = sandbox / product_id

        # Copy HTML + meta
        for name in ("index.html", "meta.json", "impressum.html", "datenschutz.html"):
            src = product_dir / name
            if src.is_file():
                shutil.copy2(src, dest / name)

        # ZIP — prefer official pack; fallback archive if compliance flakes on meta_hero
        zip_path = dest / "delivery.zip"
        try:
            data, zip_name = factory.build_client_delivery_zip(product_id)
            zip_path.write_bytes(data)
        except Exception as err:
            print(f"[WARN] {niche}: official ZIP failed ({err}); writing fallback archive")
            import zipfile

            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for path in product_dir.rglob("*"):
                    if path.is_file():
                        zf.write(path, path.relative_to(product_dir).as_posix())
            data = zip_path.read_bytes()
            zip_name = f"{case['business_name'].replace(' ', '_')}_fallback.zip"

        meta = json.loads((dest / "meta.json").read_text(encoding="utf-8"))
        # Re-evaluate commercial gate on saved HTML (post stub-pattern fix)
        from app.factory.composers import run_composers
        from app.factory.analyzer import analyze

        analysis = analyze(case["description"], niche_hint=niche)
        html = (dest / "index.html").read_text(encoding="utf-8")
        _, gate = run_composers(
            analysis,
            contacts=contacts,
            package_id="basic",
            html=html,
            scenario_id=niche,
        )
        gate_dict = gate.as_dict()
        meta["commercial_gate"] = gate_dict
        (dest / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        entry = {
            "niche": niche,
            "business_name": case["business_name"],
            "product_id": product_id,
            "headline": meta.get("business_name"),
            "preview_note": "Open local index.html in browser for visual review",
            "local_index": str((dest / "index.html").relative_to(ROOT)).replace("\\", "/"),
            "zip_bytes": len(data),
            "zip_name": zip_name,
            "hard_passed": gate.hard_passed,
            "score_passed": gate.score_passed,
            "ai_score": gate.ai_score.overall,
            "brand_leak": gate.brand_leak,
            "failures": list(gate.failures),
        }
        (dest / "MANIFEST.json").write_text(
            json.dumps(entry, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        catalog.append(entry)
        status = "OK" if gate.hard_passed and gate.score_passed else "WARN"
        print(
            f"[{status}] {niche:10} hard={entry['hard_passed']} score={entry['ai_score']} "
            f"zip={entry['zip_bytes']}B → {dest}"
        )
        if entry["failures"]:
            print(f"         failures={entry['failures']}")

    index = {
        "name": "Factory Golden Demo Set",
        "purpose": "Regression baselines before Meta Ads — do not overwrite casually",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_hint": "Compare rebuilds against questionnaire.json + MANIFEST.json",
        "niches": catalog,
    }
    (OUT / "INDEX.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT / "README.md").write_text(
        "# Factory Golden Demo Set\n\n"
        "Эталонные генерации Path A (Basic) для регрессии до/после изменений Factory.\n\n"
        "Ниши: dental · beauty · auto · restaurant · law\n\n"
        "В каждой папке: `questionnaire.json`, `meta.json`, `index.html`, "
        "`MANIFEST.json` (+ `delivery.zip` после локального generate).\n\n"
        "`delivery.zip` не коммитится (размер) — всегда пересобирается скриптом.\n\n"
        "Пересобрать:\n\n"
        "```bash\n"
        "py -3.12 scripts/generate_factory_golden_demos.py\n"
        "```\n\n"
        "Проверка регрессии:\n\n"
        "```bash\n"
        "py -3.12 -m pytest dashboard/backend/tests/test_factory_golden_demos.py -q\n"
        "```\n",
        encoding="utf-8",
    )

    # Cleanup build sandbox (artifacts copied out)
    shutil.rmtree(sandbox, ignore_errors=True)
    print(f"\nGolden set ready: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
