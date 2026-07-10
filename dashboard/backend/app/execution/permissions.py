"""Execution permission checks — every run must declare and validate grants."""

from __future__ import annotations

from app.execution.models import ExecutionPlan, PermissionGrant


class PermissionDenied(Exception):
    def __init__(self, missing: frozenset[str]) -> None:
        self.missing = missing
        super().__init__(f"Permission denied: missing {sorted(missing)}")


def validate_plan_permissions(plan: ExecutionPlan, grant: PermissionGrant) -> None:
    if plan.workspace_id and grant.workspace_id != plan.workspace_id:
        raise PermissionDenied(frozenset({"workspace_mismatch"}))
    if not grant.allows(plan.required_permissions):
        missing = plan.required_permissions - grant.kinds
        raise PermissionDenied(missing)


def union_permissions(*sets: frozenset[str]) -> frozenset[str]:
    out: set[str] = set()
    for s in sets:
        out |= set(s)
    return frozenset(out)
