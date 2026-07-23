"""S1.3 — Lightweight SAST (no external deps).

Scans security-critical Python paths for high-risk patterns.
Prints relative paths only — never dumps secrets.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = [
    ROOT / "dashboard" / "backend" / "app" / "portal",
    ROOT / "dashboard" / "backend" / "app" / "security.py",
    ROOT / "dashboard" / "backend" / "app" / "security_hardening.py",
    ROOT / "dashboard" / "backend" / "app" / "integration" / "public_chat_attachments.py",
    ROOT / "dashboard" / "backend" / "app" / "integration" / "order_materials_service.py",
]

PATTERNS = [
    (re.compile(r"\beval\s*\("), "eval"),
    (re.compile(r"\bexec\s*\("), "exec"),
    (re.compile(r"pickle\.loads\s*\("), "pickle_loads"),
    (re.compile(r"subprocess\.[A-Za-z]+\([^)]*shell\s*=\s*True"), "shell_true"),
    (re.compile(r"yaml\.load\s*\((?!.*Loader)"), "yaml_load_unsafe"),
]


def _iter_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(root.rglob("*.py"))
    return files


def main() -> int:
    hits: list[tuple[str, str]] = []
    for path in _iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for cre, label in PATTERNS:
            if cre.search(text):
                hits.append((label, str(path.relative_to(ROOT))))
    print(f"sast_hits {len(hits)}")
    for label, rel in hits[:40]:
        print(f"{label} :: {rel}")
    if hits:
        print("sast FAIL")
        return 1
    print("sast PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
