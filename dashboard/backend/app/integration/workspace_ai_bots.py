"""AI Business Bot workspace — entitlements + bot records per customer.

Store: ``{memory_dir}/customer_identity/{customer_id}/ai_bots/``
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.pricing_engine import (
    bot_package_max_bots,
    normalize_bot_package_id,
)

logger = logging.getLogger(__name__)

# Soft cap when package max_bots is None (Fair Use / Professional).
FAIR_USE_SOFT_CAP = 50

_DEFAULT_PACKAGE = "bot_starter"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bots_dir(memory_dir: Path, customer_id: str) -> Path:
    cid = str(customer_id or "").strip()
    if not cid:
        raise ValueError("customer_id_required")
    path = Path(memory_dir) / "customer_identity" / cid / "ai_bots"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _entitlements_path(memory_dir: Path, customer_id: str) -> Path:
    return _bots_dir(memory_dir, customer_id) / "entitlements.json"


def _bot_path(memory_dir: Path, customer_id: str, bot_id: str) -> Path:
    return _bots_dir(memory_dir, customer_id) / f"{bot_id}.json"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _count_bots(memory_dir: Path, customer_id: str) -> int:
    root = _bots_dir(memory_dir, customer_id)
    return sum(
        1
        for p in root.glob("*.json")
        if p.name != "entitlements.json" and p.is_file()
    )


def _effective_max(package_id: str, stored_max: int | None) -> int:
    """Resolve enforceable max: package None → Fair Use soft cap."""
    if stored_max is None:
        pkg_max = bot_package_max_bots(package_id)
        if pkg_max is None:
            return FAIR_USE_SOFT_CAP
        return int(pkg_max)
    return int(stored_max)


def get_entitlements(memory_dir: Path, customer_id: str) -> dict[str, Any]:
    """Return package entitlements including live bots_used count."""
    raw = _read_json(_entitlements_path(memory_dir, customer_id)) or {}
    package_id = normalize_bot_package_id(
        raw.get("package_id") or _DEFAULT_PACKAGE
    )
    pkg_max = bot_package_max_bots(package_id)
    # Prefer package-derived max; allow explicit override in file when set.
    if "max_bots" in raw and raw.get("max_bots") is not None:
        try:
            max_bots: int | None = int(raw["max_bots"])
        except (TypeError, ValueError):
            max_bots = pkg_max
    else:
        max_bots = pkg_max

    bots_used = _count_bots(memory_dir, customer_id)
    return {
        "package_id": package_id,
        "max_bots": max_bots,
        "bots_used": bots_used,
        "order_id": raw.get("order_id"),
        "updated_at": raw.get("updated_at"),
    }


def set_entitlements(
    memory_dir: Path,
    customer_id: str,
    package_id: str,
    order_id: str | None = None,
) -> dict[str, Any]:
    """Persist package entitlements for a customer."""
    pid = normalize_bot_package_id(package_id)
    max_bots = bot_package_max_bots(pid)
    payload: dict[str, Any] = {
        "package_id": pid,
        "max_bots": max_bots,
        "updated_at": _utc_now_iso(),
    }
    if order_id:
        payload["order_id"] = str(order_id)
    else:
        prev = _read_json(_entitlements_path(memory_dir, customer_id)) or {}
        if prev.get("order_id"):
            payload["order_id"] = prev["order_id"]
    _write_json(_entitlements_path(memory_dir, customer_id), payload)
    return get_entitlements(memory_dir, customer_id)


def list_bots(memory_dir: Path, customer_id: str) -> list[dict[str, Any]]:
    root = _bots_dir(memory_dir, customer_id)
    bots: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        if path.name == "entitlements.json":
            continue
        data = _read_json(path)
        if data:
            bots.append(data)
    return bots


def get_bot(
    memory_dir: Path,
    customer_id: str,
    bot_id: str,
) -> dict[str, Any] | None:
    bid = str(bot_id or "").strip()
    if not bid:
        return None
    return _read_json(_bot_path(memory_dir, customer_id, bid))


def create_bot(
    memory_dir: Path,
    customer_id: str,
    *,
    display_name: str,
    bot_config: dict[str, Any] | None = None,
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """Create a bot record. Enforces package max_bots (None → Fair Use soft cap 50)."""
    name = str(display_name or "").strip()
    if not name:
        return {"ok": False, "reason": "display_name_required"}

    ents = get_entitlements(memory_dir, customer_id)
    package_id = str(ents.get("package_id") or _DEFAULT_PACKAGE)
    max_bots = ents.get("max_bots")
    limit = _effective_max(package_id, max_bots if max_bots is None else int(max_bots))
    used = int(ents.get("bots_used") or 0)
    if used >= limit:
        return {
            "ok": False,
            "reason": "max_bots_reached",
            "max_bots": max_bots,
            "bots_used": used,
            "package_id": package_id,
        }

    now = _utc_now_iso()
    bot_id = f"bot-{uuid.uuid4().hex[:12]}"
    cfg = dict(bot_config or {})
    ch_list = list(channels) if channels is not None else list(cfg.get("channels") or [])
    if channels is not None:
        cfg["channels"] = ch_list
    elif "channels" not in cfg:
        cfg["channels"] = ch_list

    record: dict[str, Any] = {
        "bot_id": bot_id,
        "customer_id": str(customer_id),
        "display_name": name,
        "status": "pending_connect",
        "bot_config": cfg,
        "channels": ch_list,
        "package_id": package_id,
        "created_at": now,
        "updated_at": now,
    }
    _write_json(_bot_path(memory_dir, customer_id, bot_id), record)
    logger.info(
        "ai_bot_created customer=%s bot=%s package=%s",
        customer_id,
        bot_id,
        package_id,
    )
    return {"ok": True, "bot": record, "entitlements": get_entitlements(memory_dir, customer_id)}


def update_bot(
    memory_dir: Path,
    customer_id: str,
    bot_id: str,
    patch: dict[str, Any] | None,
) -> dict[str, Any]:
    """Apply a shallow patch to an existing bot (immutable: bot_id, customer_id, created_at)."""
    bid = str(bot_id or "").strip()
    if not bid:
        return {"ok": False, "reason": "bot_id_required"}
    existing = get_bot(memory_dir, customer_id, bid)
    if not existing:
        return {"ok": False, "reason": "bot_not_found"}

    data = dict(patch or {})
    for locked in ("bot_id", "customer_id", "created_at"):
        data.pop(locked, None)

    if "display_name" in data:
        name = str(data.get("display_name") or "").strip()
        if not name:
            return {"ok": False, "reason": "display_name_required"}
        existing["display_name"] = name

    if "status" in data and data["status"] is not None:
        existing["status"] = str(data["status"]).strip()

    if "bot_config" in data and isinstance(data["bot_config"], dict):
        merged = dict(existing.get("bot_config") or {})
        merged.update(data["bot_config"])
        existing["bot_config"] = merged

    if "channels" in data and isinstance(data["channels"], list):
        existing["channels"] = [str(c) for c in data["channels"]]
        cfg = dict(existing.get("bot_config") or {})
        cfg["channels"] = existing["channels"]
        existing["bot_config"] = cfg

    # Allow extra non-secret fields
    for key, value in data.items():
        if key in {"display_name", "status", "bot_config", "channels"}:
            continue
        if key.startswith("_"):
            continue
        existing[key] = value

    existing["updated_at"] = _utc_now_iso()
    _write_json(_bot_path(memory_dir, customer_id, bid), existing)
    return {"ok": True, "bot": existing}


def provision_from_paid_order(
    memory_dir: Path,
    customer_id: str,
    order: dict[str, Any],
) -> dict[str, Any]:
    """Set entitlements from a paid order and create the first bot from bot_config."""
    if not isinstance(order, dict):
        return {"ok": False, "reason": "order_required"}

    package_id = normalize_bot_package_id(
        order.get("package_id") or order.get("package") or _DEFAULT_PACKAGE
    )
    order_id = str(order.get("order_id") or order.get("id") or "") or None
    ents = set_entitlements(
        memory_dir,
        customer_id,
        package_id,
        order_id=order_id,
    )

    cfg = order.get("bot_config") if isinstance(order.get("bot_config"), dict) else {}
    display_name = (
        str(cfg.get("bot_display_name") or "").strip()
        or str(order.get("business_name") or "").strip()
        or "AI Business Bot"
    )
    channels = list(cfg.get("channels") or [])

    # If customer already has bots, only set entitlements (idempotent re-provision).
    existing = list_bots(memory_dir, customer_id)
    if existing:
        return {
            "ok": True,
            "provisioned": False,
            "reason": "bots_already_exist",
            "entitlements": ents,
            "bots": existing,
        }

    created = create_bot(
        memory_dir,
        customer_id,
        display_name=display_name,
        bot_config=cfg,
        channels=channels,
    )
    if not created.get("ok"):
        return {
            "ok": False,
            "reason": created.get("reason") or "create_bot_failed",
            "entitlements": ents,
        }

    bot = created["bot"]
    if order_id:
        update_bot(
            memory_dir,
            customer_id,
            bot["bot_id"],
            {"source_order_id": order_id},
        )
        bot = get_bot(memory_dir, customer_id, bot["bot_id"]) or bot

    return {
        "ok": True,
        "provisioned": True,
        "bot": bot,
        "entitlements": get_entitlements(memory_dir, customer_id),
    }


def _draft_path(memory_dir: Path, customer_id: str) -> Path:
    return _bots_dir(memory_dir, customer_id) / "order_draft.json"


def get_order_draft(memory_dir: Path, customer_id: str) -> dict[str, Any]:
    raw = _read_json(_draft_path(memory_dir, customer_id))
    if not raw:
        return {"ok": True, "draft": None}
    return {"ok": True, "draft": raw}


def save_order_draft(
    memory_dir: Path,
    customer_id: str,
    draft: dict[str, Any] | None,
) -> dict[str, Any]:
    path = _draft_path(memory_dir, customer_id)
    if not draft:
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                pass
        return {"ok": True, "draft": None}
    payload = dict(draft)
    payload["updated_at"] = _utc_now_iso()
    payload["customer_id"] = str(customer_id)
    _write_json(path, payload)
    return {"ok": True, "draft": payload}


def clear_order_draft(memory_dir: Path, customer_id: str) -> dict[str, Any]:
    return save_order_draft(memory_dir, customer_id, None)

