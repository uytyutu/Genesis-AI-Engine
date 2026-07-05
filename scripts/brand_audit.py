#!/usr/bin/env python3
"""Scan repo for legacy brand marks and list Orbit Stack v1.0 assets."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# UI/code patterns only — not docs saying "gear retired"
LEGACY_UI_PATTERNS = [
    re.compile(r"<div[^>]*connect__logo[^>]*>\s*G\s*</div>", re.I),
    re.compile(r"<span[^>]*shell__mark[^>]*>\s*G\s*</span>", re.I),
]

SCAN_EXT = {".tsx", ".ts", ".html"}
SKIP_DIRS = {"node_modules", ".git", "dist", "__pycache__", ".venv", "target", "scripts"}

ASSET_GLOBS = [
    "brand/genesis-mark-master.svg",
    "brand/genesis-mark-favicon.svg",
    "brand/generated/**/*",
    "launcher/assets/genesis.ico",
    "launcher/assets/genesis-icon.png",
    "client/desktop/public/icon.svg",
    "client/desktop/public/icon-*.png",
    "client/desktop/src-tauri/icons/*",
    "dashboard/frontend/public/brand/*",
]


def scan_legacy_ui() -> list[dict]:
    hits: list[dict] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SCAN_EXT:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pattern in LEGACY_UI_PATTERNS:
            if pattern.search(text):
                hits.append(
                    {
                        "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "issue": "Legacy letter G mark in UI",
                    }
                )
    return hits


def list_assets() -> list[str]:
    out: list[str] = []
    for pattern in ASSET_GLOBS:
        for p in ROOT.glob(pattern):
            if p.is_file() and p.name != "test-32.png":
                out.append(str(p.relative_to(ROOT)).replace("\\", "/"))
    return sorted(set(out))


def main() -> int:
    legacy = scan_legacy_ui()
    assets = list_assets()
    audit_png = ROOT / "brand" / "generated" / "audit" / "orbit-stack-size-audit.png"
    report = {
        "brand": "Genesis Brand v1.0 FROZEN — Orbit Stack",
        "ceo_approved": True,
        "legacy_ui_hits": legacy,
        "asset_count": len(assets),
        "asset_files": assets,
        "audit_sheet": str(audit_png.relative_to(ROOT)).replace("\\", "/")
        if audit_png.is_file()
        else None,
        "pass": len(legacy) == 0 and audit_png.is_file(),
    }
    out_path = ROOT / "brand" / "generated" / "audit" / "brand-ceo-approval-report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "asset_count": len(assets), "legacy_ui_hits": legacy}, indent=2))
    if legacy:
        for h in legacy:
            print(f"LEGACY: {h['file']} — {h['issue']}", file=sys.stderr)
        return 1
    print(f"OK — {len(assets)} Orbit Stack assets · {report['audit_sheet']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
