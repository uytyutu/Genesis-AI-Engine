#!/usr/bin/env python3
"""L-001 Slice 2 — Impressum readiness (prints status only, no secrets)."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

API_BASE = "http://127.0.0.1:8000"


def _fetch(path: str) -> dict:
    with urllib.request.urlopen(f"{API_BASE}{path}", timeout=10) as res:
        return json.loads(res.read().decode("utf-8"))


def main() -> int:
    try:
        status = _fetch("/api/public/legal/status")
        doc = _fetch("/api/public/legal/documents/impressum")
    except urllib.error.URLError as exc:
        print(f"FAIL backend unreachable: {exc}")
        return 1

    publishable = bool(status.get("impressum_publishable"))
    missing = status.get("missing_impressum") or []
    heading = (doc.get("sections") or [{}])[0].get("heading", "")

    print(f"impressum_publishable={str(publishable).lower()}")
    if missing:
        print("missing_fields=" + ",".join(missing))
    print(f"first_section={heading}")

    if publishable and heading != "Dokument in Vorbereitung":
        print("L-001 Slice 2: Impressum PASS")
        return 0

    print("L-001 Slice 2: Impressum NOT READY")
    print("CEO: set GENESIS_LEGAL_OPERATOR_NAME, ADDRESS_STREET, ADDRESS_ZIP, ADDRESS_CITY in dashboard/backend/.env.local")
    print("Then restart backend (Genesis.exe -> Запустить).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
