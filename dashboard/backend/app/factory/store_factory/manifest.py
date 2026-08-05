"""Store sandbox metadata + version pointers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def default_store_meta(
    *,
    order_id: str,
    product_id: str,
    template_id: str,
    pipeline: str = "generating",
) -> dict[str, Any]:
    return {
        "order_id": order_id,
        "product_id": product_id,
        "product_kind": "shop",
        "template_id": template_id,
        "pipeline": pipeline,
        "current_version": 0,
        "versions": [],
        "published": False,
        "published_at": None,
        "published_url": None,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }


def append_generation_log(product_dir: Path, event: str, detail: dict[str, Any] | None = None) -> None:
    line = {
        "ts": utc_now(),
        "event": event,
        **(detail or {}),
    }
    log_path = product_dir / "generation_log.jsonl"
    product_dir.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, ensure_ascii=False) + "\n")


def read_generation_log(product_dir: Path, *, limit: int = 50) -> list[dict[str, Any]]:
    log_path = product_dir / "generation_log.jsonl"
    if not log_path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for raw in lines[-max(1, limit) :]:
        raw = raw.strip()
        if not raw:
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def list_html_pages(product_dir: Path) -> list[str]:
    if not product_dir.is_dir():
        return []
    return sorted(p.name for p in product_dir.glob("*.html"))
