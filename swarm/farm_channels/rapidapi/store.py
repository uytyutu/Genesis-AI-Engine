"""Durable API Farm persistence — survives Genesis.exe restart."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from swarm.farm_channels.rapidapi.models import empty_candidate, empty_job, empty_revenue_event

CANDIDATES_FILE = "api_farm_candidates.json"
JOBS_FILE = "api_farm_jobs.jsonl"
REVENUE_FILE = "api_farm_revenue_events.jsonl"

_lock = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_memory_dir() -> Path:
    # Prefer dashboard backend memory (same as micro_farm_service).
    backend_mem = (
        Path(__file__).resolve().parents[3]
        / "dashboard"
        / "backend"
        / "app"
        / "memory"
    )
    if backend_mem.is_dir():
        return backend_mem
    fallback = Path(__file__).resolve().parents[2] / "memory"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


class ApiFarmStore:
    def __init__(self, memory_dir: Path | None = None) -> None:
        self.memory_dir = Path(memory_dir) if memory_dir else default_memory_dir()
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._candidates_path = self.memory_dir / CANDIDATES_FILE
        self._jobs_path = self.memory_dir / JOBS_FILE
        self._revenue_path = self.memory_dir / REVENUE_FILE

    def _read_candidates(self) -> dict[str, dict[str, Any]]:
        if not self._candidates_path.is_file():
            return {}
        try:
            data = json.loads(self._candidates_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        items = data.get("candidates") if isinstance(data, dict) else data
        if not isinstance(items, list):
            return {}
        out: dict[str, dict[str, Any]] = {}
        for row in items:
            if isinstance(row, dict) and row.get("id"):
                out[str(row["id"])] = row
        return out

    def _write_candidates(self, by_id: dict[str, dict[str, Any]]) -> None:
        payload = {
            "updated_at": _now(),
            "candidates": list(by_id.values()),
        }
        tmp = self._candidates_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._candidates_path)

    def list_candidates(self) -> list[dict[str, Any]]:
        with _lock:
            rows = list(self._read_candidates().values())
        rows.sort(key=lambda r: float(r.get("total_score") or 0), reverse=True)
        return rows

    def get_candidate(self, candidate_id: str) -> dict[str, Any] | None:
        with _lock:
            return self._read_candidates().get(str(candidate_id))

    def upsert_candidate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        with _lock:
            by_id = self._read_candidates()
            cid = str(candidate.get("id") or "").strip() or uuid.uuid4().hex[:12]
            now = _now()
            row = empty_candidate(**{**candidate, "id": cid})
            prev = by_id.get(cid)
            if prev:
                row["created_at"] = prev.get("created_at") or now
            else:
                row["created_at"] = row.get("created_at") or now
            row["updated_at"] = now
            by_id[cid] = row
            self._write_candidates(by_id)
            return row

    def update_candidate(self, candidate_id: str, **fields: Any) -> dict[str, Any] | None:
        with _lock:
            by_id = self._read_candidates()
            row = by_id.get(str(candidate_id))
            if not row:
                return None
            row = {**row, **fields, "updated_at": _now()}
            by_id[str(candidate_id)] = row
            self._write_candidates(by_id)
            return row

    def find_duplicate(self, name: str, category: str = "") -> dict[str, Any] | None:
        key = (name or "").strip().lower()
        cat = (category or "").strip().lower()
        if not key:
            return None
        for row in self.list_candidates():
            if str(row.get("name") or "").strip().lower() == key:
                if not cat or str(row.get("category") or "").strip().lower() == cat:
                    return row
        return None

    def _append_jsonl(self, path: Path, row: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            return []
        out: list[dict[str, Any]] = []
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                out.append(row)
        return out

    def enqueue_job(self, kind: str, candidate_id: str = "", **extra: Any) -> dict[str, Any]:
        with _lock:
            now = _now()
            job = empty_job(
                id=uuid.uuid4().hex[:16],
                candidate_id=candidate_id or "",
                kind=kind,
                status="queued",
                created_at=now,
                updated_at=now,
                **extra,
            )
            self._append_jsonl(self._jobs_path, job)
            return job

    def list_jobs(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with _lock:
            rows = self._read_jsonl(self._jobs_path)
        rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
        return rows[: max(1, int(limit))]

    def claim_next_job(self) -> dict[str, Any] | None:
        """Mark oldest queued job as running (rewrite file — small volume OK)."""
        with _lock:
            rows = self._read_jsonl(self._jobs_path)
            target = None
            for row in rows:
                if row.get("status") == "queued":
                    target = row
                    break
            if not target:
                return None
            now = _now()
            target["status"] = "running"
            target["started_at"] = now
            target["updated_at"] = now
            target["attempt"] = int(target.get("attempt") or 0) + 1
            self._rewrite_jobs(rows)
            return dict(target)

    def finish_job(
        self,
        job_id: str,
        *,
        ok: bool,
        result: Any = None,
        error: str = "",
    ) -> dict[str, Any] | None:
        with _lock:
            rows = self._read_jsonl(self._jobs_path)
            found = None
            for row in rows:
                if str(row.get("id")) == str(job_id):
                    row["status"] = "done" if ok else "failed"
                    row["finished_at"] = _now()
                    row["updated_at"] = row["finished_at"]
                    row["result"] = result
                    row["error"] = error or ""
                    found = dict(row)
                    break
            if found:
                self._rewrite_jobs(rows)
            return found

    def _rewrite_jobs(self, rows: list[dict[str, Any]]) -> None:
        tmp = self._jobs_path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        tmp.replace(self._jobs_path)

    def list_revenue_events(self, *, limit: int = 200) -> list[dict[str, Any]]:
        with _lock:
            rows = self._read_jsonl(self._revenue_path)
        rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
        return rows[: max(1, int(limit))]

    def get_revenue_by_external_id(self, external_id: str) -> dict[str, Any] | None:
        eid = (external_id or "").strip()
        if not eid:
            return None
        for row in self.list_revenue_events(limit=10_000):
            if str(row.get("external_id") or "") == eid:
                return row
        return None

    def append_revenue_event(self, event: dict[str, Any]) -> dict[str, Any]:
        with _lock:
            eid = str(event.get("external_id") or "").strip()
            if eid:
                for row in self._read_jsonl(self._revenue_path):
                    if str(row.get("external_id") or "") == eid:
                        return row  # idempotent
            now = _now()
            row = empty_revenue_event(**event)
            row["id"] = row.get("id") or uuid.uuid4().hex[:16]
            row["created_at"] = row.get("created_at") or now
            if not row.get("occurred_at"):
                row["occurred_at"] = now
            self._append_jsonl(self._revenue_path, row)
            return row
