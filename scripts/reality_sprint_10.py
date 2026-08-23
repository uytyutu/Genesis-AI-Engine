#!/usr/bin/env python3
"""Reality Sprint — 10 Real Companies Test (eyes only).

No internal PASS. Builds 10 niches, writes scorecards for owner eye review.

    cd dashboard/backend
    set VIRTUS_ALLOW_HTML_EXPORT=1
    py -3 scripts/../../scripts/reality_sprint_10.py

Or from repo root:
    py -3 scripts/reality_sprint_10.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
OUT = ROOT / "dashboard" / "frontend" / "public" / "reality-sprint"


def main() -> int:
    os.environ.setdefault("VIRTUS_ALLOW_HTML_EXPORT", "1")
    sys.path.insert(0, str(BACKEND))

    from app.factory.factory_service import FactoryService
    from app.factory.reality_sprint import (
        REALITY_NICHES_10,
        empty_scorecard,
        sprint_manifest,
        write_product_scorecard,
    )

    OUT.mkdir(parents=True, exist_ok=True)
    sandbox = OUT / "_sandbox"
    memory = OUT / "_memory"
    sandbox.mkdir(parents=True, exist_ok=True)
    memory.mkdir(parents=True, exist_ok=True)

    fs = FactoryService(memory_dir=memory, sandbox_dir=sandbox)
    rows: list[dict] = []

    dialogues = {
        "handwerk": (
            "Meister-Service in Berlin — Bad, Küche, Streichen. "
            "Nicht die günstigsten, aber sauber und termintreu. "
            "Dream: beste Handwerksfirma Berlins für Wohnungen."
        ),
        "dachreinigung": (
            "Dachreinigung und Imprägnierung für Einfamilienhäuser in Nürnberg. "
            "Familie, Vertrauen, Vorher/Nachher."
        ),
        "restaurant": (
            "Italienisches Familienrestaurant in München mit Abendreservierung und Lieferung."
        ),
        "psychology": (
            "Psychologe in Berlin — Schwerpunkt Angst, Online-Sitzungen, ruhige Atmosphäre."
        ),
        "dental": "Moderne Zahnarztpraxis in Hamburg — Angstpatienten willkommen, Online-Termin.",
        "law": "Kanzlei für Familienrecht in Köln — klar, menschlich, erstes Gespräch.",
        "beauty": "Friseursalon in Frankfurt — moderne Looks, Online-Buchung Pflicht.",
        "auto": "Autowerkstatt in Stuttgart — Diagnose, Reifen, WhatsApp mit Fotos.",
        "fitness": "Personal Training Studio in Düsseldorf — Pläne und Buchung.",
        "realestate": "Immobilienmakler in Berlin — Verkauf und Vermietung, klare Exposés.",
    }

    print("Reality Sprint — building 10 niches for EYE review…", flush=True)
    for niche in REALITY_NICHES_10:
        intent = f"reality-{niche}-{datetime.now(timezone.utc).strftime('%H%M%S')}"
        contacts = {
            "niche": niche,
            "city": "Berlin",
            "market_code": "DE",
            "package_id": "standalone",
            "commerce_mode": "standalone",
            "dialogue": dialogues.get(niche, f"Unternehmen in der Nische {niche}."),
            "fabricate_company": True,
            "demo_gallery": True,
            "business_interview": {
                "free_text": dialogues.get(niche, ""),
                "niche": niche,
                "city": "Berlin",
                "dream_vision": "In fünf Jahren Referenzmarke der Region sein.",
            },
        }
        try:
            summary = fs.build_landing(
                description=dialogues.get(niche, niche),
                intent_id=intent,
                package_id="standalone",
                market_code="DE",
                contacts=contacts,
            )
            pid = str(summary.get("product_id") or intent)
            name = str(summary.get("business_name") or niche)
            card = empty_scorecard(
                niche_id=niche,
                product_id=pid,
                company_name=name,
                preview_url=f"/reality-sprint/_sandbox/{pid}/index.html",
            )
            product_dir = sandbox / pid
            if product_dir.is_dir():
                write_product_scorecard(product_dir, card)
            rows.append(
                {
                    "niche": niche,
                    "product_id": pid,
                    "company_name": name,
                    "status": summary.get("status"),
                    "overall": "PENDING_OWNER",
                    "preview": f"_sandbox/{pid}/index.html",
                    "scorecard": f"_sandbox/{pid}/REALITY_SCORECARD.md",
                    "law4": (summary.get("law4") if isinstance(summary, dict) else None),
                }
            )
            print(f"  OK  {niche:16} → {name} [{summary.get('status')}]", flush=True)
        except Exception as exc:
            rows.append(
                {
                    "niche": niche,
                    "product_id": "",
                    "company_name": "",
                    "status": "error",
                    "overall": "FAIL",
                    "error": str(exc)[:200],
                }
            )
            print(f"  ERR {niche:16} → {exc}", flush=True)

    manifest = sprint_manifest(rows)
    (OUT / "REALITY_SPRINT.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    md = OUT / "REALITY_SPRINT.md"
    lines = [
        "# Reality Sprint — 10 Real Companies Test",
        "",
        f"Generated: {manifest['generated_at']}",
        "",
        "> Would a real German business owner say: **Ja — genau so einen Auftritt will ich?**",
        "",
        "Fill each `REALITY_SCORECARD.md` with your eyes. No JSON PASS counts.",
        "",
        "| # | Niche | Company | Preview | Scorecard | Eye verdict |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for i, r in enumerate(rows, 1):
        lines.append(
            f"| {i} | `{r.get('niche')}` | {r.get('company_name') or '—'} | "
            f"`{r.get('preview') or '—'}` | `{r.get('scorecard') or '—'}` | PENDING_OWNER |"
        )
    lines.extend(
        [
            "",
            "## Gate",
            "",
            "- ≥8/10 PASS by owner eye → continue",
            "- <8/10 → stop features; fix generation only",
            "- Law №4 confuse-pair → REBUILD",
            "",
            "Canon: `docs/canon/VIRTUS_CORE_REALITY_SPRINT.md`",
            "",
        ]
    )
    md.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {md}", flush=True)
    print("Open each preview, cover the logo, fill scorecards. Eyes only.", flush=True)
    return 0 if all(r.get("status") != "error" for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
