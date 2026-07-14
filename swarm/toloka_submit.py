"""Submit Genesis farm labels to Toloka Pipeline API v2 (dataset items + optional run)."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from swarm.adapter_toloka import TolokaAdapter
from swarm.exchange_circuit_breaker import ExchangeCircuitBreaker
from swarm.farm_error_ledger import FarmErrorLedger

logger = logging.getLogger(__name__)

DEFAULT_DATASET_NAME = "virtus-core-labels"
STATE_FILENAME = "toloka_submit_state.json"
BATCH_MAX = 50

DATASET_FIELDS: list[dict[str, Any]] = [
    {"name": "task_id", "jsonSchema": {"type": "string"}},
    {"name": "source_id", "jsonSchema": {"type": "string"}},
    {"name": "labels_json", "jsonSchema": {"type": "string"}},
    {"name": "company", "jsonSchema": {"type": "string"}},
    {"name": "url", "jsonSchema": {"type": "string"}},
    {"name": "exported_at", "jsonSchema": {"type": "string"}},
]


def _truthy_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "")
    if not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class TolokaLabelSubmitter:
    """Reads swarm_labels_export.jsonl and pushes pending rows to Toloka dataset."""

    def __init__(
        self,
        *,
        memory_dir: Path,
        adapter: TolokaAdapter | None = None,
        opportunity_lookup: Any | None = None,
    ) -> None:
        self._memory = memory_dir
        self._adapter = adapter or TolokaAdapter()
        self._opp_lookup = opportunity_lookup
        self._export_path = memory_dir / "swarm_labels_export.jsonl"
        self._state_path = memory_dir / STATE_FILENAME
        self._breaker = ExchangeCircuitBreaker(memory_dir, exchange_id="toloka")
        self._error_ledger = FarmErrorLedger(memory_dir)

    def error_ledger_summary(self) -> dict[str, Any]:
        return self._error_ledger.summary()

    def _log_reject(
        self,
        *,
        stage: str,
        message: str,
        http_status: int | None = None,
        batch_size: int = 0,
        sample_task_ids: list[str] | None = None,
    ) -> None:
        try:
            self._error_ledger.append(
                exchange="toloka",
                stage=stage,
                message=message or "reject",
                http_status=http_status,
                batch_size=batch_size,
                sample_task_ids=sample_task_ids,
            )
        except OSError:
            logger.exception("farm_error_ledger append failed")

    def circuit_breaker_snapshot(self) -> dict[str, Any]:
        return self._breaker.snapshot()

    def auto_submit_enabled(self) -> bool:
        if self._breaker.safe_mode():
            return False
        vault_live = os.getenv("FARM_LIVE_MODE", "").strip().lower() == "live"
        if os.getenv("TOLOKA_AUTO_SUBMIT", "").strip():
            return _truthy_env("TOLOKA_AUTO_SUBMIT", default=False)
        return vault_live and self._adapter.configured()

    def load_state(self) -> dict[str, Any]:
        if not self._state_path.is_file():
            return {"submitted_task_ids": [], "last_submit_at": None, "last_error": None}
        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return {"submitted_task_ids": [], "last_submit_at": None, "last_error": None}
            data.setdefault("submitted_task_ids", [])
            return data
        except (json.JSONDecodeError, OSError):
            return {"submitted_task_ids": [], "last_submit_at": None, "last_error": None}

    def save_state(self, state: dict[str, Any]) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        ids = state.get("submitted_task_ids") or []
        if len(ids) > 5000:
            state["submitted_task_ids"] = ids[-5000:]
        self._state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def status(self) -> dict[str, Any]:
        state = self.load_state()
        pending = len(self._pending_records())
        submitted = len(state.get("submitted_task_ids") or [])
        conn = self._adapter.check_connection()
        return {
            "configured": self._adapter.configured(),
            "auto_submit_enabled": self.auto_submit_enabled(),
            "connected": bool(conn.get("connected")),
            "pending_count": pending,
            "submitted_count": submitted,
            "project_id": os.getenv("TOLOKA_PROJECT_ID", "").strip() or state.get("project_id"),
            "dataset_id": os.getenv("TOLOKA_DATASET_ID", "").strip() or state.get("dataset_id"),
            "pipeline_id": os.getenv("TOLOKA_PIPELINE_ID", "").strip() or state.get("pipeline_id"),
            "last_submit_at": state.get("last_submit_at"),
            "last_run_id": state.get("last_run_id"),
            "last_error": state.get("last_error"),
            "last_batch_count": state.get("last_batch_count"),
            "last_run_status": state.get("last_run_status"),
            "pipeline_success_count": int(state.get("pipeline_success_count") or 0),
            "circuit_breaker": self._breaker.snapshot(),
            "message": conn.get("message"),
        }

    def _pending_records(self) -> list[dict[str, Any]]:
        if not self._export_path.is_file():
            return []
        state = self.load_state()
        done = {str(x) for x in (state.get("submitted_task_ids") or [])}
        pending: list[dict[str, Any]] = []
        for line in self._export_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            tid = str(row.get("task_id") or "")
            if not tid or tid in done:
                continue
            pending.append(row)
        return pending

    def _enrich_row(self, row: dict[str, Any]) -> dict[str, Any]:
        task_id = str(row.get("task_id") or "")
        company = str(row.get("company") or "")
        url = str(row.get("url") or "")
        if self._opp_lookup and task_id and (not company or not url):
            try:
                opp = self._opp_lookup.get(task_id)
                if isinstance(opp, dict):
                    company = company or str(opp.get("company_name") or "")
                    url = url or str(opp.get("website_url") or "")
            except Exception:
                pass
        labels = row.get("labels")
        if not isinstance(labels, dict):
            labels = {}
        return {
            "task_id": task_id,
            "source_id": str(row.get("source_id") or "asset_scan"),
            "labels_json": json.dumps(labels, ensure_ascii=False),
            "company": company,
            "url": url,
            "exported_at": str(row.get("exported_at") or datetime.now(timezone.utc).isoformat()),
        }

    def _resolve_project_id(self, state: dict[str, Any]) -> tuple[str | None, str | None]:
        env_pid = os.getenv("TOLOKA_PROJECT_ID", "").strip()
        if env_pid:
            return env_pid, None
        cached = str(state.get("project_id") or "").strip()
        if cached:
            return cached, None
        listed = self._adapter.list_projects(limit=20)
        if not listed.get("ok"):
            return None, listed.get("message") or "Не удалось получить проекты Toloka"
        projects = listed.get("projects") or []
        active = [p for p in projects if isinstance(p, dict) and p.get("status") == "active"]
        pick = (active or projects)[0] if projects else None
        if not pick:
            return None, "В Toloka нет проектов — создай проект на platform.toloka.ai"
        return str(pick.get("id") or ""), None

    def _resolve_dataset_id(self, project_id: str, state: dict[str, Any]) -> tuple[str | None, str | None]:
        env_did = os.getenv("TOLOKA_DATASET_ID", "").strip()
        if env_did:
            return env_did, None
        cached = str(state.get("dataset_id") or "").strip()
        if cached:
            return cached, None
        listed = self._adapter.list_project_datasets(project_id, limit=50)
        if not listed.get("ok"):
            return None, listed.get("message") or "Не удалось получить datasets"
        datasets = listed.get("datasets") or []
        for ds in datasets:
            if isinstance(ds, dict) and str(ds.get("name") or "") == DEFAULT_DATASET_NAME:
                return str(ds.get("id") or ""), None
        created = self._adapter.create_dataset(project_id, name=DEFAULT_DATASET_NAME)
        if not created.get("ok"):
            return None, created.get("message") or "Не удалось создать dataset"
        return str((created.get("dataset") or {}).get("id") or ""), None

    def _resolve_pipeline_id(self, project_id: str, state: dict[str, Any]) -> str | None:
        env_pid = os.getenv("TOLOKA_PIPELINE_ID", "").strip()
        if env_pid:
            return env_pid
        cached = str(state.get("pipeline_id") or "").strip()
        if cached:
            return cached
        listed = self._adapter.list_project_pipelines(project_id, limit=20)
        if not listed.get("ok"):
            return None
        pipelines = listed.get("pipelines") or []
        if not pipelines:
            return None
        first = pipelines[0]
        if isinstance(first, dict):
            return str(first.get("id") or "") or None
        return None

    def _poll_run_status(self, run_id: str, state: dict[str, Any]) -> None:
        polled = self._adapter.get_pipeline_run(run_id)
        if not polled.get("ok"):
            return
        run = polled.get("run") if isinstance(polled.get("run"), dict) else {}
        status = str(run.get("status") or "")
        state["last_run_status"] = status
        state["last_run_polled_at"] = datetime.now(timezone.utc).isoformat()

    def submit_pending(self, *, limit: int = BATCH_MAX, trigger_run: bool | None = None) -> dict[str, Any]:
        if self._breaker.safe_mode():
            snap = self._breaker.snapshot()
            msg = f"Safe Mode Toloka · {snap.get('safe_mode_reason') or 'circuit open'}"
            self._log_reject(stage="safe_mode", message=msg)
            return {
                "ok": False,
                "message": f"Safe Mode Toloka · {snap.get('safe_mode_reason') or 'circuit open'}",
                "submitted": 0,
                "safe_mode": True,
                "circuit_breaker": snap,
            }
        if not self._adapter.configured():
            return {"ok": False, "message": "TOLOKA_API_TOKEN не задан", "submitted": 0}
        conn = self._adapter.check_connection()
        if not conn.get("connected"):
            return {"ok": False, "message": conn.get("message") or "Toloka offline", "submitted": 0}

        pending = self._pending_records()[: max(1, min(BATCH_MAX, int(limit)))]
        if not pending:
            return {"ok": True, "message": "Нечего отправлять — очередь пуста", "submitted": 0, "pending": 0}

        state = self.load_state()
        project_id, err = self._resolve_project_id(state)
        if err or not project_id:
            state["last_error"] = err
            self.save_state(state)
            self._log_reject(stage="resolve_project", message=str(err or "project_id missing"))
            return {"ok": False, "message": err or "project_id missing", "submitted": 0}

        dataset_id, err = self._resolve_dataset_id(project_id, state)
        if err or not dataset_id:
            state["last_error"] = err
            state["project_id"] = project_id
            self.save_state(state)
            self._log_reject(stage="resolve_dataset", message=str(err or "dataset_id missing"))
            return {"ok": False, "message": err or "dataset_id missing", "submitted": 0}

        items = [self._enrich_row(row) for row in pending]
        added = self._adapter.add_dataset_items(dataset_id, items=items, fields=DATASET_FIELDS)
        if not added.get("ok"):
            opened = self._breaker.record_failure(
                error=str(added.get("message") or "add_dataset_items"),
                http_status=int(added.get("http_status") or 0) or None,
            )
            self._log_reject(
                stage="add_dataset_items",
                message=str(added.get("message") or "Toloka reject"),
                http_status=int(added.get("http_status") or 0) or None,
                batch_size=len(pending),
                sample_task_ids=[str(r.get("task_id") or "") for r in pending[:5]],
            )
            state["last_error"] = added.get("message")
            state["project_id"] = project_id
            state["dataset_id"] = dataset_id
            self.save_state(state)
            return {
                "ok": False,
                "message": added.get("message") or "Toloka reject",
                "submitted": 0,
                "http_status": added.get("http_status"),
                "safe_mode": opened,
                "circuit_breaker": self._breaker.snapshot(),
            }

        self._breaker.record_success()

        submitted_ids = state.setdefault("submitted_task_ids", [])
        for row in pending:
            tid = str(row.get("task_id") or "")
            if tid and tid not in submitted_ids:
                submitted_ids.append(tid)

        state["project_id"] = project_id
        state["dataset_id"] = dataset_id
        state["last_submit_at"] = datetime.now(timezone.utc).isoformat()
        state["last_batch_count"] = len(pending)
        state["last_error"] = None

        run_id = None
        do_run = trigger_run if trigger_run is not None else _truthy_env("TOLOKA_TRIGGER_RUN", default=True)
        pipeline_id = self._resolve_pipeline_id(project_id, state)
        if pipeline_id:
            state["pipeline_id"] = pipeline_id
        if do_run and pipeline_id:
            attached = self._adapter.attach_pipeline_dataset(pipeline_id, dataset_id=dataset_id)
            if attached.get("ok"):
                run = self._adapter.start_pipeline_run(pipeline_id)
                if run.get("ok"):
                    run_id = (run.get("run") or {}).get("id")
                    state["last_run_id"] = run_id
                    if run_id:
                        self._poll_run_status(str(run_id), state)
                        run_st = str(state.get("last_run_status") or "").lower()
                        if run_st in {"succeeded", "success", "completed"}:
                            state["pipeline_success_count"] = int(state.get("pipeline_success_count") or 0) + 1
                        elif run_st in {"failed", "error", "cancelled"}:
                            self._log_reject(
                                stage="pipeline_run",
                                message=f"pipeline run {run_id} status={run_st}",
                                batch_size=len(pending),
                            )
                elif not run.get("ok"):
                    self._log_reject(
                        stage="start_pipeline_run",
                        message=str(run.get("message") or "start run failed"),
                    )
            elif not attached.get("ok"):
                self._log_reject(
                    stage="attach_pipeline_dataset",
                    message=str(attached.get("message") or "attach failed"),
                )

        self.save_state(state)
        remaining = len(self._pending_records())
        return {
            "ok": True,
            "message": f"Toloka приняла {len(pending)} разметок · dataset {dataset_id[:12]}…",
            "submitted": len(pending),
            "pending": remaining,
            "project_id": project_id,
            "dataset_id": dataset_id,
            "pipeline_id": pipeline_id,
            "run_id": run_id,
            "http_status": added.get("http_status"),
        }
