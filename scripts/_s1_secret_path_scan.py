"""S1 secret-path scan — prints labels + relative paths only (no secret values)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "node_modules", ".next", "dist", "__pycache__", ".venv", "venv", "branding"}
EXTS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
    ".ps1",
    ".sh",
    ".env",
    ".example",
}
PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "openai_sk_like"),
    (re.compile(r"sk_live_[A-Za-z0-9]+"), "stripe_live_like"),
    (re.compile(r"sk_test_[A-Za-z0-9]+"), "stripe_test_like"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{20,}"), "google_api_like"),
]


def main() -> None:
    hits: list[tuple[str, str]] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.name.startswith(".env") and path.name not in {".env.example", ".env.sample"}:
            hits.append(("env_file_present", str(path.relative_to(ROOT))))
            continue
        if path.suffix.lower() not in EXTS and not path.name.startswith(".env"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for cre, label in PATTERNS:
            if cre.search(text):
                hits.append((label, str(path.relative_to(ROOT))))
                break
    print(f"hit_count {len(hits)}")
    for label, rel in hits[:60]:
        print(f"{label} :: {rel}")


if __name__ == "__main__":
    main()
