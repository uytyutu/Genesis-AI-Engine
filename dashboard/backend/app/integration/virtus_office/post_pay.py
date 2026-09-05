"""CC-3 — post-pay progress steps + cabinet summary helpers."""

from __future__ import annotations

from typing import Any


def progress_steps(job: dict[str, Any]) -> list[dict[str, Any]]:
    """Ordered UI steps for Ihre Bestellung after payment."""
    status = str(job.get("status") or "")
    payment = dict(job.get("payment") or {})
    paid = bool(payment.get("paid")) or status in {
        "paid",
        "executing",
        "quality_check",
        "completed",
    }
    quality = dict(job.get("quality") or {})
    qa_failed = status == "failed" and str(job.get("failure_reason") or "") == "quality_gate_failed"
    exec_failed = status == "failed" and not qa_failed

    def state(done: bool, active: bool, failed: bool = False) -> str:
        if failed:
            return "failed"
        if done:
            return "done"
        if active:
            return "active"
        return "pending"

    steps = [
        {
            "id": "paid",
            "label_de": "Zahlung bestätigt",
            "state": state(paid, False),
        },
        {
            "id": "executing",
            "label_de": "Auftrag wird bearbeitet",
            "state": state(
                status in {"quality_check", "completed"} or (qa_failed),
                status in {"paid", "executing"} and paid and not exec_failed,
                failed=exec_failed and status == "failed" and not qa_failed,
            ),
        },
        {
            "id": "quality",
            "label_de": "Qualitätsprüfung",
            "state": state(
                status == "completed" or (qa_failed and bool(quality)),
                status == "quality_check",
                failed=qa_failed,
            ),
        },
        {
            "id": "done",
            "label_de": "Fertig",
            "state": state(status == "completed", False, failed=False),
        },
    ]
    return steps


def download_formats(job: dict[str, Any], *, download_ready: bool) -> list[dict[str, Any]]:
    """Available download buttons — only the produced format is enabled."""
    artifact = dict(job.get("artifact") or {})
    ext = str(artifact.get("ext") or "").lower().lstrip(".")
    formats = ("pdf", "docx", "xlsx", "zip")
    out: list[dict[str, Any]] = []
    for fmt in formats:
        available = download_ready and ext == fmt
        out.append(
            {
                "format": fmt,
                "label": fmt.upper(),
                "available": available,
                "url": (
                    f"/api/office/jobs/{job['job_id']}/artifact?format={fmt}"
                    if available
                    else None
                ),
            }
        )
    return out


def cabinet_summary(job: dict[str, Any], *, download_ready: bool = False) -> dict[str, Any]:
    payment = dict(job.get("payment") or {})
    proposal = dict(job.get("proposal") or {})
    artifact = dict(job.get("artifact") or {})
    return {
        "job_id": job.get("job_id"),
        "status": job.get("status"),
        "filename": job.get("filename"),
        "task": proposal.get("task") or (job.get("understanding") or {}).get("intent", {}).get("id"),
        "task_label_de": proposal.get("task_label_de"),
        "price_eur": payment.get("price_eur")
        or (payment.get("price_lock") or {}).get("price_eur")
        or proposal.get("price_eur"),
        "paid": bool(payment.get("paid")),
        "payment_status": payment.get("status"),
        "order_id": payment.get("order_id"),
        "artifact_ext": artifact.get("ext"),
        "artifact_filename": artifact.get("filename"),
        "download_ready": download_ready,
        "failure_reason": job.get("failure_reason"),
        "failure_detail": job.get("failure_detail"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "progress": progress_steps(job),
    }
