#!/usr/bin/env python3
"""Persist Gewerbe / legal operator from env into memory/legal_entity.json."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKEND = REPO / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from app.env_loader import load_local_env  # noqa: E402
from app.legal.entity_store import LegalEntityStore  # noqa: E402


def main() -> int:
    load_local_env()
    memory = BACKEND / "memory"
    store = LegalEntityStore(memory)
    cfg = store.load()
    status = store.status()

    if not status["impressum_publishable"]:
        missing = status.get("missing_impressum") or []
        print("impressum_publishable=false")
        print("missing_fields=" + ",".join(missing))
        print("Add fields to dashboard/backend/.env.local (see env.legal.example), then rerun.")
        return 1

    cfg.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    store.save(cfg)
    print("impressum_publishable=true")
    print(f"entity_path={status['entity_path']}")
    print("L-001 Slice 2: legal entity saved from env")
    return 0


if __name__ == "__main__":
    sys.exit(main())
