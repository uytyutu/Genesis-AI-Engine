"""Virtus Video AI persistence — accounts, jobs, ledger (memory JSON)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class VieworaStore:
    def __init__(self, memory_dir: Path) -> None:
        self._root = memory_dir / "viewora"
        self._root.mkdir(parents=True, exist_ok=True)
        self._accounts = self._root / "accounts.json"
        self._jobs = self._root / "jobs.jsonl"
        self._orders = self._root / "orders.jsonl"

    def _load_accounts(self) -> dict[str, Any]:
        if not self._accounts.is_file():
            return {"accounts": {}}
        try:
            return json.loads(self._accounts.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"accounts": {}}

    def _save_accounts(self, data: dict[str, Any]) -> None:
        self._accounts.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_or_create_account(self, account_id: str | None = None) -> dict[str, Any]:
        data = self._load_accounts()
        accounts = data.setdefault("accounts", {})
        aid = (account_id or "").strip() or f"guest_{uuid.uuid4().hex[:12]}"
        if aid not in accounts:
            accounts[aid] = {
                "id": aid,
                "plan_id": "free",
                "credits": 0,
                "free_creations_left": 3,
                "email": "",
                "created_at": _now(),
                "updated_at": _now(),
                "orders": [],
            }
            self._save_accounts(data)
        return dict(accounts[aid])

    def save_account(self, account: dict[str, Any]) -> dict[str, Any]:
        data = self._load_accounts()
        accounts = data.setdefault("accounts", {})
        aid = str(account.get("id") or "")
        if not aid:
            raise ValueError("account_id_required")
        account["updated_at"] = _now()
        accounts[aid] = account
        self._save_accounts(data)
        return dict(account)

    def append_job(self, job: dict[str, Any]) -> dict[str, Any]:
        row = dict(job)
        row.setdefault("id", f"vj_{uuid.uuid4().hex[:14]}")
        row.setdefault("created_at", _now())
        with self._jobs.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def list_jobs(self, account_id: str, *, limit: int = 40) -> list[dict[str, Any]]:
        if not self._jobs.is_file():
            return []
        out: list[dict[str, Any]] = []
        try:
            lines = self._jobs.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(row.get("account_id") or "") == account_id:
                out.append(row)
            if len(out) >= limit:
                break
        return out

    def append_order(self, order: dict[str, Any]) -> dict[str, Any]:
        row = dict(order)
        row.setdefault("id", f"vo_{uuid.uuid4().hex[:14]}")
        row.setdefault("created_at", _now())
        with self._orders.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        if not self._orders.is_file():
            return None
        try:
            lines = self._orders.read_text(encoding="utf-8").splitlines()
        except OSError:
            return None
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(row.get("id") or "") == order_id:
                return row
        return None

    def mark_order_paid(self, order_id: str, *, payment_mode: str) -> dict[str, Any] | None:
        order = self.get_order(order_id)
        if not order:
            return None
        order = dict(order)
        order["paid"] = True
        order["paid_at"] = _now()
        order["payment_mode"] = payment_mode
        with self._orders.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(order, ensure_ascii=False) + "\n")
        return order
