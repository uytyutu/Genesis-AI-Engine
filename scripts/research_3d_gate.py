#!/usr/bin/env python3
"""Research 3D gate harness — isolated from Path A commerce.

Usage (repo root):
  py -3.12 scripts/research_3d_gate.py
  py -3.12 scripts/research_3d_gate.py --fixture
  py -3.12 scripts/research_3d_gate.py --scene dashboard/backend/_research_3d/scenes/dental

Writes report JSON under dashboard/backend/_research_3d/artifacts/ (gitignored).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
RESEARCH = BACKEND / "_research_3d"
sys.path.insert(0, str(BACKEND))

from app.factory.research_3d.fallback_spec import resolve_delivery_mode  # noqa: E402
from app.factory.research_3d.glb_budget import check_glb_budget  # noqa: E402
from app.factory.research_3d.license_gate import check_asset_license  # noqa: E402
from app.factory.research_3d.niche_catalog import niche_coverage  # noqa: E402


def _ensure_fixture_glb(fixture_dir: Path) -> Path:
    """Tiny fake .glb (not valid glTF) — size gate only for smoke."""
    fixture_dir.mkdir(parents=True, exist_ok=True)
    glb = fixture_dir / "hero.glb"
    if not glb.is_file():
        # Minimal bytes under budget; real glTF validation is a later research step.
        glb.write_bytes(b"glTF-research-fixture\x00" + b"\x00" * 256)
    return glb


def gate_scene(scene_dir: Path, *, webgl_ok: bool = True) -> dict:
    lic = check_asset_license(scene_dir)
    glb = scene_dir / "hero.glb"
    if not glb.is_file():
        glbs = list(scene_dir.glob("*.glb")) + list(scene_dir.glob("*.gltf"))
        glb = glbs[0] if glbs else glb
    budget = check_glb_budget(glb) if glb.is_file() else check_glb_budget(glb)
    mode = resolve_delivery_mode(
        webgl_ok=webgl_ok,
        license_ok=lic.ok,
        budget_ok=budget.ok,
        want_3d=True,
    )
    return {
        "scene_dir": str(scene_dir),
        "license": {"ok": lic.ok, "code": lic.code, "detail": lic.detail},
        "budget": {
            "ok": budget.ok,
            "code": budget.code,
            "bytes": budget.bytes_used,
            "limit": budget.limit,
            "detail": budget.detail,
        },
        "delivery_mode": mode,
        "path_a_safe": mode != "webgl_3d" or (lic.ok and budget.ok),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Research 3D license/budget/fallback gate")
    parser.add_argument(
        "--scene",
        type=str,
        default="",
        help="Path to scenes/<niche> with LICENSE + CREDITS + hero.glb",
    )
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="Run against built-in _fixture scene",
    )
    parser.add_argument(
        "--no-webgl",
        action="store_true",
        help="Simulate WebGL unavailable → expect css_motion",
    )
    args = parser.parse_args()

    coverage = niche_coverage()
    print("research_3d coverage:", json.dumps(coverage, ensure_ascii=False))

    if args.fixture or not args.scene:
        scene_dir = RESEARCH / "scenes" / "_fixture"
        _ensure_fixture_glb(scene_dir)
    else:
        scene_dir = Path(args.scene)
        if not scene_dir.is_absolute():
            scene_dir = (ROOT / scene_dir).resolve()

    report = gate_scene(scene_dir, webgl_ok=not args.no_webgl)
    report["at"] = datetime.now(timezone.utc).isoformat()
    report["isolated_from_path_a"] = True

    art = RESEARCH / "artifacts"
    art.mkdir(parents=True, exist_ok=True)
    out = art / f"gate_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("wrote", out)

    # Fixture / happy path should be able to select webgl_3d when webgl ok
    if args.no_webgl:
        return 0 if report["delivery_mode"] == "css_motion" else 1
    if report["license"]["ok"] and report["budget"]["ok"]:
        return 0 if report["delivery_mode"] == "webgl_3d" else 1
    # Empty niche folder: expected fail until assets added
    return 0 if report["delivery_mode"] in ("classic", "css_motion") else 1


if __name__ == "__main__":
    raise SystemExit(main())
