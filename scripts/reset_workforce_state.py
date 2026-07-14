"""Reset local workforce quota/circuit/health cache (dev only)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "dashboard" / "backend" / "memory" / "workforce"


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "quotas.json").write_text(
        json.dumps({"date": date.today().isoformat(), "used": {}}),
        encoding="utf-8",
    )
    (ROOT / "circuit_breaker.json").write_text(
        json.dumps({"providers": {}}),
        encoding="utf-8",
    )
    (ROOT / "health.json").write_text(
        json.dumps({"employees": {}, "updated_at": "reset"}),
        encoding="utf-8",
    )
    print("workforce state reset:", ROOT)


if __name__ == "__main__":
    main()
