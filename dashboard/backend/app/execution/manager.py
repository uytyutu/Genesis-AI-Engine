"""Execution Manager — central orchestrator (Phase 1)."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from app.execution.capabilities import ExecutionCapabilityRegistry
from app.execution.log_store import ExecutionLogStore
from app.execution.models import (
    ExecutionPlan,
    ExecutionResult,
    ExecutionStatus,
    PermissionGrant,
    RollbackStrategy,
    StepExecutionRecord,
)
from app.execution.permissions import PermissionDenied, validate_plan_permissions
from app.execution.verifier import VerificationError, verify_step
from app.execution.workspace import ExecutionWorkspaceStore


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutionManager:
    """
    Plan → Execute → Observe → Verify → Repair → Complete.

    Does not modify Genesis Brain. Call from future Executive hook or owner API.
    """

    def __init__(
        self,
        *,
        registry: ExecutionCapabilityRegistry | None = None,
        workspace_store: ExecutionWorkspaceStore,
        log_store: ExecutionLogStore,
    ) -> None:
        self._registry = registry or ExecutionCapabilityRegistry()
        self._workspaces = workspace_store
        self._logs = log_store

    def run(self, plan: ExecutionPlan, grant: PermissionGrant) -> ExecutionResult:
        validate_plan_permissions(plan, grant)
        if plan.workspace_id and not self._workspaces.get(plan.workspace_id):
            raise PermissionDenied(frozenset({"workspace_not_found"}))

        started = _utc_now()
        t0 = time.perf_counter()
        result = ExecutionResult(
            plan_id=plan.plan_id or f"run-{uuid.uuid4().hex[:12]}",
            goal=plan.goal,
            workspace_id=plan.workspace_id,
            status="running",
            started_at=started,
        )

        completed: dict[str, dict[str, Any]] = {}
        ordered = self._topological_order(plan)

        for step in ordered:
            record = self._execute_step(step, plan, grant, completed)
            result.steps.append(record)
            if plan.workspace_id:
                self._logs.append_step_log(plan.workspace_id, record)

            if record.status == "completed":
                completed[step.id] = record.outputs
                continue

            if plan.rollback != RollbackStrategy.NONE:
                self._attempt_rollback(result.steps, plan)
            result.status = record.status
            result.error = record.error or record.verification_error
            result.finished_at = _utc_now()
            result.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            self._logs.save_run(result)
            return result

        result.status = "completed"
        result.finished_at = _utc_now()
        result.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
        if plan.workspace_id:
            self._workspaces.touch(plan.workspace_id)
        self._logs.save_run(result)
        return result

    def _execute_step(
        self,
        step,
        plan: ExecutionPlan,
        grant: PermissionGrant,
        completed: dict[str, dict[str, Any]],
    ) -> StepExecutionRecord:
        cap = self._registry.get(step.capability_id)
        started = _utc_now()
        t0 = time.perf_counter()

        if cap is None:
            return self._failed_record(step, started, t0, f"unknown capability: {step.capability_id}")

        if not grant.allows(cap.permissions):
            missing = cap.permissions - grant.kinds
            return self._failed_record(step, started, t0, f"permission denied: {sorted(missing)}")

        if not self._registry.is_executable(step.capability_id):
            return StepExecutionRecord(
                step_id=step.id,
                capability_id=step.capability_id,
                status="blocked",
                started_at=started,
                finished_at=_utc_now(),
                duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                inputs=step.inputs,
                error=f"capability not implemented (phase {cap.phase}): {step.capability_id}",
            )

        inputs = self._resolve_inputs(step.inputs, completed)
        last_error: str | None = None
        for attempt in range(step.max_retries + 1):
            try:
                executor = self._registry.get_executor(step.capability_id)
                if not executor:
                    return self._failed_record(step, started, t0, "executor not registered")
                outputs = executor.execute(
                    inputs,
                    {"workspace_id": plan.workspace_id, "goal": plan.goal, "grant": grant.to_dict()},
                )
                record = StepExecutionRecord(
                    step_id=step.id,
                    capability_id=step.capability_id,
                    status="completed",
                    started_at=started,
                    finished_at=_utc_now(),
                    duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                    inputs=inputs,
                    outputs=outputs,
                    retry_count=attempt,
                )
                try:
                    verify_step(record, step.verification)
                    record.verified = True
                except VerificationError as exc:
                    record.status = "failed"
                    record.verified = False
                    record.verification_error = str(exc)
                    record.error = str(exc)
                    last_error = str(exc)
                    if attempt < step.max_retries:
                        continue
                    return record
                return record
            except Exception as exc:  # noqa: BLE001 — execution boundary
                last_error = str(exc)
                if attempt < step.max_retries:
                    continue
                return self._failed_record(step, started, t0, last_error, inputs=inputs, retry=attempt)

        return self._failed_record(step, started, t0, last_error or "execution failed", inputs=inputs)

    def _failed_record(
        self,
        step,
        started: str,
        t0: float,
        error: str,
        *,
        inputs: dict | None = None,
        retry: int = 0,
    ) -> StepExecutionRecord:
        return StepExecutionRecord(
            step_id=step.id,
            capability_id=step.capability_id,
            status="failed",
            started_at=started,
            finished_at=_utc_now(),
            duration_ms=round((time.perf_counter() - t0) * 1000, 2),
            inputs=inputs or step.inputs,
            error=error,
            retry_count=retry,
        )

    def _resolve_inputs(self, inputs: dict[str, Any], completed: dict[str, dict[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, val in inputs.items():
            if isinstance(val, str) and val.startswith("{{") and val.endswith("}}"):
                ref = val[2:-2].strip()
                step_id, _, field = ref.partition(".")
                if step_id in completed and field in completed[step_id]:
                    out[key] = completed[step_id][field]
                else:
                    out[key] = val
            else:
                out[key] = val
        return out

    def _topological_order(self, plan: ExecutionPlan) -> list:
        steps = {s.id: s for s in plan.steps}
        done: set[str] = set()
        ordered: list = []

        while len(ordered) < len(plan.steps):
            progress = False
            for sid, step in steps.items():
                if sid in done:
                    continue
                if all(dep in done for dep in step.depends_on):
                    ordered.append(step)
                    done.add(sid)
                    progress = True
            if not progress:
                raise ValueError("cyclic or missing dependencies in execution plan")
        return ordered

    def _attempt_rollback(self, steps: list[StepExecutionRecord], plan: ExecutionPlan) -> None:
        for record in reversed(steps):
            if record.status != "completed":
                continue
            cap = self._registry.get(record.capability_id)
            if not cap or not cap.supports_rollback:
                continue
            if not self._registry.is_executable(record.capability_id):
                continue
            executor = self._registry.get_executor(record.capability_id)
            if executor and hasattr(executor, "rollback"):
                try:
                    executor.rollback(record.inputs, record.outputs)
                    record.status = "rolled_back"
                except Exception:
                    pass
            if plan.rollback == RollbackStrategy.REVERT_LAST_STEP:
                break
