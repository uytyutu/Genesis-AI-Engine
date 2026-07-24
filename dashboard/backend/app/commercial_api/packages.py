"""API Product packages — subscription-style prepaid plans (not hardcoded in debit logic)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACKAGES_FILE = "commercial_api_packages.json"

# Editable defaults — override via memory JSON
DEFAULT_PACKAGES: dict[str, dict[str, Any]] = {
    "starter": {
        "id": "starter",
        "name": "Starter",
        "price_eur": 24.0,
        "balance_eur": 24.5,
        "scopes": ["audit"],
        "included": {"audit": 50},
        "note_ru": "Audit · ~50 запросов prepaid",
        "best_for_ru": "Первый тестовый клиент API",
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price_eur": 190.0,
        "balance_eur": 190.0,
        "scopes": ["audit", "leads"],
        "included": {"audit": 400, "leads": 100},
        "note_ru": "Audit + Leads",
        "best_for_ru": "Агентства и регулярный поток аудитов",
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise",
        "price_eur": 990.0,
        "balance_eur": 990.0,
        "scopes": ["audit", "leads", "factory", "*"],
        "included": {"audit": "high", "leads": "high", "factory": "included"},
        "note_ru": "Factory · Agents · расширенные лимиты",
        "best_for_ru": "White-label / B2B интеграции",
    },
}


def load_packages(memory_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    packages = {k: dict(v) for k, v in DEFAULT_PACKAGES.items()}
    if memory_dir is None:
        return packages
    path = memory_dir / PACKAGES_FILE
    if not path.is_file():
        return packages
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return packages
    if not isinstance(raw, dict):
        return packages
    for key, val in raw.items():
        if key.startswith("_") or not isinstance(val, dict):
            continue
        base = packages.get(key, {"id": key})
        merged = dict(base)
        merged.update(val)
        merged["id"] = key
        packages[key] = merged
    return packages


def list_packages(memory_dir: Path | None = None) -> list[dict[str, Any]]:
    return list(load_packages(memory_dir).values())


def get_package(package_id: str, memory_dir: Path | None = None) -> dict[str, Any] | None:
    return load_packages(memory_dir).get(str(package_id or "").strip())


def save_default_packages_file(memory_dir: Path) -> Path:
    path = memory_dir / PACKAGES_FILE
    if path.is_file():
        return path
    payload = {
        "_comment": "Edit package prices/scopes without changing Gateway code.",
        **DEFAULT_PACKAGES,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
