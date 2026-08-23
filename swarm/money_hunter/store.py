"""JSONL store for Money Hunter opportunities + events."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from swarm.money_hunter.models import SOURCE_ADAPTERS, STATUSES
from swarm.money_hunter.profit import compute_economics, priority_key

OPPS_FILE = "money_hunter_opportunities.jsonl"
EVENTS_FILE = "money_hunter_events.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MoneyHunterStore:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)
        self._memory.mkdir(parents=True, exist_ok=True)

    def _opps_path(self) -> Path:
        return self._memory / OPPS_FILE

    def _events_path(self) -> Path:
        return self._memory / EVENTS_FILE

    def emit(
        self,
        event: str,
        *,
        opportunity_id: str = "",
        execution_id: str = "",
        cost: float = 0.0,
        status: str = "",
        extra: dict[str, Any] | None = None,
    ) -> None:
        row = {
            "timestamp": _now(),
            "event": event,
            "opportunity_id": opportunity_id,
            "execution_id": execution_id,
            "cost": float(cost or 0),
            "status": status,
            **(extra or {}),
        }
        with open(self._events_path(), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _load(self) -> list[dict[str, Any]]:
        path = self._opps_path()
        if not path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows

    def _save(self, rows: list[dict[str, Any]]) -> None:
        path = self._opps_path()
        with open(path, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def list_all(self) -> list[dict[str, Any]]:
        return self._load()

    def get(self, opportunity_id: str) -> dict[str, Any] | None:
        oid = str(opportunity_id or "").strip()
        for row in self._load():
            if row.get("id") == oid:
                return row
        return None

    def upsert(self, row: dict[str, Any]) -> dict[str, Any]:
        rows = self._load()
        oid = row.get("id")
        for i, prev in enumerate(rows):
            if prev.get("id") == oid:
                rows[i] = row
                self._save(rows)
                return row
        rows.append(row)
        self._save(rows)
        return row

    def dedupe_key(self, url: str, title: str, external_id: str) -> str:
        if external_id:
            return f"ext:{external_id.strip().lower()}"
        u = (url or "").strip().lower().rstrip("/")
        if u:
            return f"url:{u}"
        return f"title:{(title or '').strip().lower()[:120]}"

    def find_duplicate(self, *, url: str, title: str, external_id: str) -> dict[str, Any] | None:
        key = self.dedupe_key(url, title, external_id)
        for row in self._load():
            k = self.dedupe_key(
                str(row.get("url") or ""),
                str(row.get("title") or ""),
                str(row.get("external_id") or ""),
            )
            if k == key:
                return row
        return None

    def import_opportunity(self, payload: dict[str, Any]) -> dict[str, Any]:
        source = str(payload.get("source") or "manual").strip().lower()
        if source not in SOURCE_ADAPTERS:
            # Accept marketplace names as *_manual.
            alt = f"{source}_manual" if not source.endswith("_manual") else source
            if alt in SOURCE_ADAPTERS:
                source = alt
            else:
                source = "manual"

        title = str(payload.get("title") or "").strip()
        description = str(payload.get("description") or "").strip()
        url = str(payload.get("url") or "").strip()
        external_id = str(payload.get("external_id") or "").strip()
        if not title and not description:
            raise ValueError("title_or_description_required")

        dup = self.find_duplicate(url=url, title=title, external_id=external_id)
        if dup and dup.get("status") not in ("REJECTED", "CANCELLED", "FAILED"):
            return {**dup, "_deduped": True}

        now = _now()
        eco_input = {
            **payload,
            "source": source,
            "title": title,
            "description": description,
            "first_money_mode": bool(payload.get("first_money_mode", True)),
        }
        economics = compute_economics(eco_input)
        decision = economics.get("decision") or "MAYBE"
        if decision == "REJECT":
            status = "REJECTED"
        elif decision == "GO":
            status = "PENDING_APPROVAL"
        else:
            status = "QUALIFIED"

        category = str(payload.get("category") or _guess_category(title, description))
        row = {
            "id": f"mh-{uuid.uuid4().hex[:12]}",
            "source": source,
            "source_adapter": SOURCE_ADAPTERS[source],
            "external_id": external_id,
            "url": url,
            "title": title or description[:80],
            "description": description,
            "category": category,
            "client_name": str(payload.get("client_name") or "").strip(),
            "deadline": str(payload.get("deadline") or "").strip(),
            "status": status,
            "economics": economics,
            "budget_min": economics["budget_min"],
            "budget_max": economics["budget_max"],
            "currency": economics["currency"],
            "expected_revenue": economics["expected_revenue"],
            "expected_cost": economics["expected_cost"],
            "expected_profit": economics["expected_profit"],
            "opportunity_score": economics["opportunity_score"],
            "automation_percent": economics["automation_percent"],
            "success_probability": economics["success_probability"],
            "execution_plan": None,
            "proposal": None,
            "delivery": None,
            "approval": None,
            "paid_settlement": None,
            "real_revenue_eur": 0.0,
            "created_at": now,
            "updated_at": now,
            "first_money_mode": bool(payload.get("first_money_mode", True)),
            "events_tail": [],
        }
        if status not in STATUSES:
            row["status"] = "DISCOVERED"

        self.upsert(row)
        self.emit("opportunity_discovered", opportunity_id=row["id"], status=status)
        self.emit(
            "opportunity_analyzed",
            opportunity_id=row["id"],
            status=status,
            cost=float(economics.get("expected_cost") or 0),
            extra={"decision": decision, "score": economics.get("opportunity_score")},
        )
        if status == "REJECTED":
            self.emit(
                "opportunity_rejected",
                opportunity_id=row["id"],
                status=status,
                extra={"reasons": economics.get("reject_reasons")},
            )
        elif status in ("QUALIFIED", "PENDING_APPROVAL"):
            self.emit("opportunity_qualified", opportunity_id=row["id"], status=status)
        return row

    def top(self, *, limit: int = 20, first_money: bool = True) -> list[dict[str, Any]]:
        rows = [
            r
            for r in self._load()
            if r.get("status")
            in ("PENDING_APPROVAL", "QUALIFIED", "APPROVED", "EXECUTING", "DISCOVERED")
        ]
        if first_money:
            # Prefer first-money band but do not hide others entirely.
            rows.sort(
                key=lambda r: (
                    0
                    if 30 <= float((r.get("economics") or {}).get("expected_revenue") or 0) <= 150
                    else 1,
                    priority_key(r),
                )
            )
        else:
            rows.sort(key=priority_key)
        return rows[: max(1, min(100, limit))]

    def set_status(
        self,
        opportunity_id: str,
        status: str,
        *,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if status not in STATUSES:
            raise ValueError("invalid_status")
        row = self.get(opportunity_id)
        if not row:
            raise ValueError("not_found")
        row["status"] = status
        row["updated_at"] = _now()
        if extra:
            row.update(extra)
        self.upsert(row)
        return row


def _guess_category(title: str, description: str) -> str:
    text = f"{title}\n{description}".lower()
    mapping = (
        ("WEB_RESEARCH", ("research", "recherche", "lookup")),
        ("MARKET_RESEARCH", ("market", "markt", "competitor", "конкурент")),
        ("DATA_CLEANING", ("csv", "clean", "dedupe", "spreadsheet")),
        ("CONTENT_QA", ("qa", "proofread", "copy edit")),
        ("IMAGE_CLASSIFICATION", ("image", "classify", "label photo")),
        ("DATA_VERIFICATION", ("verify", "validation", "check data")),
    )
    for cat, words in mapping:
        if any(w in text for w in words):
            return cat
    return "WEB_RESEARCH"
