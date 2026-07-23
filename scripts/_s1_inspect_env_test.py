"""Inspect tracked .env.test — key names + metadata only."""
from pathlib import Path

p = Path("dashboard/backend/.env.test")
for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        continue
    key, raw = s.split("=", 1)
    val = raw.strip().strip("\"'")
    sens = any(x in key.upper() for x in ("KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL"))
    placeholder = (
        not val
        or val.lower() in {"changeme", "test", "fake", "xxx"}
        or "fake" in val.lower()
        or "example" in val.lower()
        or val.startswith("sk_test_fake")
    )
    print(f"{key}\tsensitive={sens}\tlen={len(val)}\tplaceholderish={placeholder}")
