#!/usr/bin/env python3
"""Product Mind v1 — consultant responses, not page navigation."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))
os.environ["GENESIS_ACCEPTANCE_GATE"] = "1"

from app.integration.genesis_brain import GenesisBrain  # noqa: E402

MUST_HAVE = (
    "под ключ",
    "studio",
    "два путь",
    "два пути",
)
MUST_NOT = (
    "/services",
    "/products",
    "перейдите в раздел",
    "купите pro",
    "basic 49",
)

SCENARIOS = [
    ("car-wash", "У меня автомойка", ("автомойк", "telegram", "crm")),
    ("coffee", "Хочу открыть кофейню", ("кофейн", "под ключ")),
    ("shop", "Хочу интернет-магазин", ("магазин", "подписка", "не нужн")),
    ("one-site", "Нужен один сайт для салона", ("подписка", "не нужн")),
    ("multi", "Планирую создавать много сайтов каждый месяц", ("studio", "окуп")),
]


def main() -> int:
    tmp = ROOT / "memory" / "product_mind_gate_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    brain = GenesisBrain(memory_dir=tmp, packages=[])
    results = []

    for sid, prompt, hints in SCENARIOS:
        r = brain.chat(
            system="",
            messages=[{"role": "user", "content": prompt}],
            visitor_id=f"pm-{sid}",
        )
        low = r.answer.lower()
        violations = [m for m in MUST_NOT if m in low]
        if not any(h in low for h in hints):
            violations.append(f"missing_hints:{hints}")
        if sid != "multi" and not any(m in low for m in MUST_HAVE if m != "studio"):
            if "под ключ" not in low and "два" not in low:
                violations.append("not_consultant_style")
        results.append(
            {
                "id": sid,
                "pass": not violations,
                "violations": violations,
                "preview": r.answer[:280],
            }
        )

    passed = sum(1 for x in results if x["pass"])
    out = {"total": len(results), "passed": passed, "results": results}
    path = ROOT / "scripts" / "product_mind_gate_results.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Product Mind gate: {passed}/{len(results)} PASS")
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  [{status}] {r['id']}")
        for v in r["violations"]:
            print(f"       - {v}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
