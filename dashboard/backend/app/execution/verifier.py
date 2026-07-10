"""Step output verification — no assumed success."""

from __future__ import annotations

from app.execution.models import ExecutionStatus, StepExecutionRecord, VerificationRule


class VerificationError(Exception):
    pass


def verify_step(record: StepExecutionRecord, rule: VerificationRule | None) -> None:
    if record.status != "completed":
        if rule and rule.expect_status and record.status != rule.expect_status:
            raise VerificationError(f"expected status {rule.expect_status}, got {record.status}")
        if record.status == "failed":
            raise VerificationError(record.error or "step failed")
        return
    if not rule:
        return
    for key in rule.required_output_keys:
        if key not in record.outputs:
            raise VerificationError(f"missing output key: {key}")
