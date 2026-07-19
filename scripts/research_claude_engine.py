#!/usr/bin/env python3
"""Research harness: Classic vs Claude Factory engines (not Path A commerce).

Usage (from repo root):
  py -3.12 scripts/research_claude_engine.py
  py -3.12 scripts/research_claude_engine.py --engines classic
  py -3.12 scripts/research_claude_engine.py --engines classic,claude --limit 3

Writes artifacts under dashboard/backend/_research_claude_engine/ (gitignored).
Claude requires GENESIS_ANTHROPIC_API_KEY or OpenRouter key — hard fail, no Classic fallback.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from app.factory.engines.base import ClaudeEngineAuthError, EngineError, EngineRequest  # noqa: E402
from app.factory.engines.router import generate_with_engine  # noqa: E402
from app.factory.engines.animated_research_pricing import (  # noqa: E402
    list_animated_research_prices,
)

OUT_DIR = BACKEND / "_research_claude_engine"

BRIEFS: list[dict] = [
    {
        "id": "dental",
        "business_name": "Smile Dental Austin",
        "market_code": "US",
        "language": "en",
        "city": "Austin",
        "phone": "+1 512 555 0100",
        "description": "Family dental clinic in Austin TX. Cleanings, implants, emergency care. Warm professional tone.",
    },
    {
        "id": "autoservice",
        "business_name": "AutoFix Berlin",
        "market_code": "DE",
        "language": "de",
        "city": "Berlin",
        "phone": "+49 30 555 0100",
        "description": "Kfz-Werkstatt in Berlin. Inspektion, Bremsen, Reifenwechsel. Schnell und ehrlich.",
    },
    {
        "id": "restaurant",
        "business_name": "Trattoria Luna",
        "market_code": "IT",
        "language": "en",
        "city": "Milan",
        "phone": "+39 02 555 0100",
        "description": "Italian restaurant in Milan. Fresh pasta, wine list, evening reservations.",
    },
    {
        "id": "saas",
        "business_name": "LedgerFlow",
        "market_code": "US",
        "language": "en",
        "city": "San Francisco",
        "description": "B2B SaaS for invoice automation. Clear pricing CTA, trust for finance teams.",
    },
    {
        "id": "lawyer",
        "business_name": "Hartmann Rechtsanwälte",
        "market_code": "DE",
        "language": "de",
        "city": "München",
        "phone": "+49 89 555 0200",
        "description": "Wirtschaftskanzlei München. Vertragsrecht, GmbH, Startup-Beratung.",
    },
    {
        "id": "accountant",
        "business_name": "ZahlenKlar Steuerberatung",
        "market_code": "DE",
        "language": "de",
        "city": "Hamburg",
        "description": "Steuerberatung für Freelancer und GmbH in Hamburg. Jahresabschluss, Elster, Beratung.",
    },
    {
        "id": "construction",
        "business_name": "BuildRight Construction",
        "market_code": "GB",
        "language": "en",
        "city": "Manchester",
        "phone": "+44 161 555 0100",
        "description": "Residential construction and renovations in Manchester. Project gallery CTA.",
    },
    {
        "id": "fitness",
        "business_name": "Pulse Fitness Studio",
        "market_code": "US",
        "language": "en",
        "city": "Denver",
        "description": "Boutique fitness studio. HIIT, personal training, membership CTA.",
    },
    {
        "id": "beauty",
        "business_name": "Atelier Beauté",
        "market_code": "FR",
        "language": "en",
        "city": "Lyon",
        "description": "Beauty salon in Lyon. Hair, nails, skincare. Booking-focused landing.",
    },
    {
        "id": "it_agency",
        "business_name": "Northbyte Agency",
        "market_code": "UA",
        "language": "uk",
        "city": "Kyiv",
        "description": "IT агентство в Києві. Веб, мобільні додатки, дизайн. Портфоліо та CTA на консультацію.",
    },
]


def _zip_bytes(html: str, name: str = "index.html") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(name, html)
        zf.writestr(
            "README_RESEARCH.txt",
            "Virtus Core research artifact — not a commercial Path A delivery.\n",
        )
    return buf.getvalue()


def _artifact_names(engine: str) -> tuple[str, str, str]:
    """Return (html_name, zip_name, meta_name) with research prefixes."""
    if engine == "claude":
        prefix = "claude_research_"
    else:
        prefix = "classic_research_"
    return f"{prefix}index.html", f"{prefix}site.zip", f"{prefix}meta.json"


def _run_one(engine: str, brief: dict, run_dir: Path) -> dict:
    req = EngineRequest(
        description=brief["description"],
        business_name=brief["business_name"],
        market_code=brief.get("market_code", "DE"),
        language=brief.get("language", "en"),
        package_id="business",
        city=brief.get("city", ""),
        phone=brief.get("phone", ""),
        email=brief.get("email", ""),
    )
    niche_dir = run_dir / brief["id"] / engine
    niche_dir.mkdir(parents=True, exist_ok=True)
    html_name, zip_name, meta_name = _artifact_names(engine)
    started = time.perf_counter()
    row: dict = {
        "brief_id": brief["id"],
        "engine": engine,
        "ok": False,
        "elapsed_sec": None,
        "html_bytes": None,
        "zip_bytes": None,
        "file_count": 2,
        "error": None,
        "preview": None,
        "html_file": html_name,
        "zip_file": zip_name,
    }
    try:
        result = generate_with_engine(engine, req)
        elapsed = time.perf_counter() - started
        html_path = niche_dir / html_name
        html_path.write_text(result.html, encoding="utf-8")
        zdata = _zip_bytes(result.html)
        (niche_dir / zip_name).write_bytes(zdata)
        meta = {
            **row,
            "ok": True,
            "elapsed_sec": round(elapsed, 3),
            "html_bytes": len(result.html.encode("utf-8")),
            "zip_bytes": len(zdata),
            "preview": str(html_path.relative_to(run_dir)),
            "engine_meta": result.meta,
        }
        (niche_dir / meta_name).write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return meta
    except ClaudeEngineAuthError as exc:
        elapsed = time.perf_counter() - started
        row["elapsed_sec"] = round(elapsed, 3)
        row["error"] = {"code": exc.code, "message": exc.message, "type": "ClaudeEngineAuthError"}
        (niche_dir / meta_name).write_text(
            json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return row
    except EngineError as exc:
        elapsed = time.perf_counter() - started
        row["elapsed_sec"] = round(elapsed, 3)
        row["error"] = {"code": exc.code, "message": exc.message}
        (niche_dir / meta_name).write_text(
            json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return row
    except Exception as exc:  # noqa: BLE001 — research harness must record any failure
        elapsed = time.perf_counter() - started
        row["elapsed_sec"] = round(elapsed, 3)
        row["error"] = {"code": "unexpected", "message": str(exc)}
        (niche_dir / meta_name).write_text(
            json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return row


def _print_prices() -> int:
    rows = list_animated_research_prices()
    print("Animated Landing — RESEARCH prices only (NOT in Path A checkout)")
    print(f"{'Market':<6} {'Cur':<5} {'Basic':<14} {'Business':<14} {'Premium':<14}")
    for row in rows:
        pkgs = row["packages"]
        print(
            f"{row['market_code']:<6} {row['currency']:<5} "
            f"{pkgs['basic']['animated_label']:<14} "
            f"{pkgs['business']['animated_label']:<14} "
            f"{pkgs['premium']['animated_label']:<14}"
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "animated_research_prices.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {out} (gitignored folder)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Classic vs Claude Factory research harness")
    parser.add_argument(
        "--engines",
        default="classic,claude",
        help="Comma list: classic,claude",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit briefs (0 = all 10)")
    parser.add_argument(
        "--prices-only",
        action="store_true",
        help="Print research Animated prices per market and exit (no generation)",
    )
    args = parser.parse_args()
    if args.prices_only:
        return _print_prices()

    engines = [e.strip().lower() for e in args.engines.split(",") if e.strip()]
    briefs = BRIEFS[: args.limit] if args.limit and args.limit > 0 else BRIEFS

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = OUT_DIR / stamp
    run_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    for brief in briefs:
        for engine in engines:
            print(f"-> {brief['id']} / {engine} ...", flush=True)
            row = _run_one(engine, brief, run_dir)
            status = "OK" if row.get("ok") else f"FAIL:{row.get('error')}"
            print(f"  {status}  {row.get('elapsed_sec')}s  bytes={row.get('html_bytes')}", flush=True)
            results.append(row)

    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "engines": engines,
        "brief_count": len(briefs),
        "results": results,
        "note": (
            "Research only — Path A commerce unchanged. "
            "Decide Animated package only after CEO quality review."
        ),
    }
    (run_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nSummary: {run_dir / 'summary.json'}", flush=True)

    classic_ok = sum(1 for r in results if r["engine"] == "classic" and r.get("ok"))
    claude_ok = sum(1 for r in results if r["engine"] == "claude" and r.get("ok"))
    print(f"Classic OK: {classic_ok}  Claude OK: {claude_ok}", flush=True)
    if "claude" in engines and claude_ok == 0:
        # Auth/hard fail is expected without key — do not imply Path A broke.
        return 2 if classic_ok == len(briefs) or "classic" not in engines else 1
    return 0 if ("classic" not in engines or classic_ok == len(briefs)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
