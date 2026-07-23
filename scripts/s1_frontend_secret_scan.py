"""S1 — Frontend secret scan (source + optional .next build).

Scans for key-like strings. Prints relative paths only — never secret values.
Exit code 1 if high-risk patterns found outside allowlisted fixtures.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "dashboard" / "frontend"
SKIP_DIR_NAMES = {".git", "node_modules", "dist", "__pycache__", "cache"}
ALLOW_EXACT = frozenset({"sk_test_fake", "sk_test_abc", "sk_live_abc"})

PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "openai_sk"),
    (re.compile(r"sk_live_[A-Za-z0-9]{8,}"), "stripe_live"),
    (re.compile(r"sk_test_[A-Za-z0-9]{8,}"), "stripe_test"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{20,}"), "google_api"),
    (re.compile(r"BEGIN (RSA |OPENSSH )?PRIVATE KEY"), "private_key"),
]

SCAN_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".json", ".map"}


def _should_skip(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def main() -> int:
    roots = [FRONTEND / "app", FRONTEND / "lib"]
    next_dir = FRONTEND / ".next"
    if next_dir.is_dir():
        roots.append(next_dir)

    hits: list[tuple[str, str]] = []
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or _should_skip(path):
                continue
            if path.suffix.lower() not in SCAN_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for cre, label in PATTERNS:
                m = cre.search(text)
                if not m:
                    continue
                if m.group(0) in ALLOW_EXACT:
                    continue
                hits.append((label, str(path.relative_to(ROOT))))
                break

    print(f"frontend_secret_hits {len(hits)}")
    for label, rel in hits[:40]:
        print(f"{label} :: {rel}")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
