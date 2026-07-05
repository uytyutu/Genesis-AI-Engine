#!/usr/bin/env python3
"""CLI entry — refresh desktop shortcut + icon cache (called from build.ps1)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from launcher.desktop_identity import ensure_desktop_identity
from launcher import paths

if __name__ == "__main__":
    root = paths.find_project_root()
    result = ensure_desktop_identity(root, force_cache=True)
    print(result.message)
    if result.shortcut_path:
        print(f"Shortcut: {result.shortcut_path}")
    if not result.ok:
        raise SystemExit(1)
