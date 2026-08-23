#!/usr/bin/env python3
"""Sprint: Reality Benchmark — control set of 18 demos for eye review.

Law #2: Reality Over Architecture.
No new Directors. No new Engines. Calls existing sync only.

Sites (× Starter/Business/Premium): psychology, dental, law
Stores (× Starter/Business/Premium): fashion, electronics, furniture

Gate: if ≥5 of 18 look template-like by human eye → stop new features;
fix generation only.

    py -3.12 scripts/reality_benchmark.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "scripts" / "sync_public_package_previews.py"
PUBLIC = ROOT / "dashboard" / "frontend" / "public" / "package-previews"
BASE = "http://127.0.0.1:3001"

SITE_FOLDERS = ("psychology", "dental", "law")
STORE_FOLDERS = ("fashion", "electronics", "furniture")
TIERS = ("basic", "business", "premium")
TIER_LABEL = {"basic": "Starter", "business": "Business", "premium": "Premium"}

CHECK_AXES = (
    "first_screen",
    "brand",
    "composition",
    "typography",
    "atmosphere",
    "business_vs_virtus",
    "premium_studio",
    "store_want_to_buy",
)


def _run(args: list[str]) -> int:
    print("+", " ".join(args), flush=True)
    return int(subprocess.run(args, cwd=str(ROOT)).returncode or 0)


def demo_rows() -> list[dict]:
    rows: list[dict] = []
    for tier in TIERS:
        for folder in SITE_FOLDERS:
            rows.append(
                {
                    "id": f"site:{tier}:{folder}",
                    "kind": "site",
                    "tier": tier,
                    "tier_label": TIER_LABEL[tier],
                    "niche": folder,
                    "url": f"{BASE}/package-previews/sites/{tier}/{folder}/index.html",
                    "path": f"sites/{tier}/{folder}/index.html",
                    "template_like": None,
                    "scores": {k: None for k in CHECK_AXES if k != "store_want_to_buy"},
                    "notes": "",
                }
            )
    for tier in TIERS:
        for folder in STORE_FOLDERS:
            rows.append(
                {
                    "id": f"store:{tier}:{folder}",
                    "kind": "store",
                    "tier": tier,
                    "tier_label": TIER_LABEL[tier],
                    "niche": folder,
                    "url": f"{BASE}/package-previews/stores/{tier}/{folder}/index.html",
                    "path": f"stores/{tier}/{folder}/index.html",
                    "template_like": None,
                    "scores": {
                        k: None
                        for k in CHECK_AXES
                        if k not in ("business_vs_virtus",)
                    },
                    "notes": "",
                }
            )
    return rows


def write_checklist(rows: list[dict]) -> Path:
    out = PUBLIC / "REALITY_BENCHMARK.json"
    payload = {
        "sprint": "Creative Identity Generation",
        "law": "Law #2 — Reality Over Architecture · No idea → no HTML",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "demo_count": len(rows),
        "gate_ru": (
            "Нет Creative Identity (идеи, которую можно почувствовать) — HTML запрещён. "
            "Если демо читаются как шаблон ниши — FAIL. Новые функции запрещены."
        ),
        "gate_en": (
            "No felt Creative Identity → no HTML. "
            "Niche-template demos → FAIL. New features forbidden."
        ),
        "question_ru": (
            "Чувствуется ли идея бренда (Silent Forest / Fire & Smoke…), "
            "а не просто «сайт психолога»?"
        ),
        "owner_review": "PENDING_OWNER",
        "reality_benchmark": "FAIL",
        "reality_note": (
            "Owner: template feel / missing artistic concept. "
            "Marketing HTML frozen — Creative Identity Owner Preview only."
        ),
        "template_like_count": None,
        "check_axes": list(CHECK_AXES),
        "demos": rows,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = PUBLIC / "REALITY_BENCHMARK.md"
    lines = [
        "# Reality Benchmark — 18 demos",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Gate",
        "",
        payload["gate_ru"],
        "",
        "## Question",
        "",
        payload["question_ru"],
        "",
        "## Sites",
        "",
    ]
    for r in rows:
        if r["kind"] != "site":
            continue
        lines.append(
            f"- [ ] **{r['tier_label']} · {r['niche']}** — {r['url']}"
        )
    lines.extend(["", "## Stores", ""])
    for r in rows:
        if r["kind"] != "store":
            continue
        lines.append(
            f"- [ ] **{r['tier_label']} · {r['niche']}** — {r['url']}"
        )
    lines.extend(
        [
            "",
            "## Eye checklist (each demo)",
            "",
            "- First screen stops the eye?",
            "- Real company / brand feeling?",
            "- Designer composition?",
            "- Typography fits the niche?",
            "- Atmosphere / emotion?",
            "- Business ≥ Virtus Core `/site`?",
            "- Premium = expensive digital studio?",
            "- Store: want to buy here?",
            "",
            "Mark `template_like` in REALITY_BENCHMARK.json while reviewing.",
            "",
        ]
    )
    md.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Reality Benchmark — 18 demos")
    parser.add_argument(
        "--checklist-only",
        action="store_true",
        help="Only write checklist URLs (no regenerate)",
    )
    args = parser.parse_args()
    py = sys.executable
    rows = demo_rows()

    if not args.checklist_only:
        rc = _run(
            [
                py,
                str(SYNC),
                "--tiers",
                "basic,business,premium",
                "--folders",
                ",".join(SITE_FOLDERS),
                "--websites-only",
            ]
        )
        if rc != 0:
            return rc
        rc = _run(
            [
                py,
                str(SYNC),
                "--stores-only",
                "--store-tiers",
                "basic,business,premium",
                "--store-folders",
                ",".join(STORE_FOLDERS),
            ]
        )
        if rc != 0:
            return rc

    path = write_checklist(rows)
    missing = []
    for r in rows:
        if not (PUBLIC / r["path"]).is_file():
            missing.append(r["path"])

    print()
    print("=== Reality Benchmark ===")
    print(f"Demos: {len(rows)}")
    print(f"Checklist: {path}")
    print(f"Markdown: {PUBLIC / 'REALITY_BENCHMARK.md'}")
    if missing:
        print(f"MISSING {len(missing)} files:")
        for m in missing:
            print(f"  - {m}")
        return 2
    print()
    print("Open http://127.0.0.1:3001 and review with eyes.")
    print("Gate: ≥5 template-like → stop features, fix generation only.")
    print("Owner review stays PENDING until human critique.")
    for r in rows:
        print(f"  {r['id']}: {r['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
