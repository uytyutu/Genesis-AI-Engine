#!/usr/bin/env python3
"""Internal check — Finish Desktop Identity (Cursor runs this, not CEO)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from launcher.branding import ico_path, mark_png_path
from launcher.desktop_identity import _exe_path, _shortcut_path, ensure_desktop_identity
from launcher import paths
from launcher.deps import frontend_build_integrity, frontend_build_ready


def main() -> int:
    root = paths.find_project_root()
    errors: list[str] = []
    checks: list[str] = []

    exe = _exe_path(root)
    if not exe or not exe.is_file():
        errors.append("dist/Genesis.exe missing")
    else:
        checks.append(f"exe OK: {exe} ({exe.stat().st_size} bytes)")

    ico = ico_path()
    if not ico.is_file():
        errors.append("launcher/assets/genesis.ico missing")
    else:
        checks.append(f"ico OK: {ico}")

    if not mark_png_path().is_file():
        errors.append("launcher/assets/genesis-icon.png missing")
    else:
        checks.append("launcher mark PNG OK")

    try:
        from launcher.branding import load_mark_pil_image

        pil = load_mark_pil_image()
        if pil is None:
            errors.append("load_mark_pil_image returned None")
        else:
            from PIL import Image

            if not isinstance(pil, Image.Image):
                errors.append("load_mark_pil_image must return PIL.Image")
            else:
                checks.append("CTkImage-safe PIL mark OK")
    except Exception as exc:
        errors.append(f"load_mark_pil_image failed: {exc}")

    brand_dir = root / "dashboard" / "frontend" / "public" / "brand"
    for name in ("favicon-32.png", "icon-192.png", "genesis-mark.svg"):
        p = brand_dir / name
        if not p.is_file():
            errors.append(f"missing {p.relative_to(root)}")
        else:
            checks.append(f"web brand OK: {name}")

    if not frontend_build_ready(root):
        errors.append(".next production build missing — run npm run build")
    elif not frontend_build_integrity(root):
        errors.append(".next corrupt — rebuild frontend")
    else:
        checks.append("frontend production build OK")

    result = ensure_desktop_identity(root, force_cache=False)
    if not result.ok:
        errors.append(result.message)
    else:
        checks.append(result.message)
        if result.shortcut_path:
            checks.append(f"shortcut: {result.shortcut_path}")

    print("=== Virtus Core Desktop Identity Verify ===")
    for line in checks:
        print(f"  OK  {line}")
    for line in errors:
        print(f"  FAIL {line}")

    if errors:
        print(f"\n{len(errors)} check(s) failed.")
        return 1
    print("\nAll automated checks passed. CEO path: double-click Genesis.exe (Virtus Core launcher).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
