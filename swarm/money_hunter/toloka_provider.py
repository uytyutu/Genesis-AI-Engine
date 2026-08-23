"""Toloka as Execution Provider (Spend) — never a revenue source."""

from __future__ import annotations

from typing import Any


class TolokaProvider:
    """estimate → CEO approval → create. No auto-spend."""

    def estimate_cost(self, *, hours: float = 1.0, rate_eur: float = 4.0) -> dict[str, Any]:
        h = max(0.1, float(hours or 1.0))
        cost = round(h * float(rate_eur or 4.0), 2)
        return {
            "ok": True,
            "estimated_cost_eur": cost,
            "hours": h,
            "rate_eur": rate_eur,
            "role": "requester_spend",
            "is_revenue": False,
        }

    def create_task(self, *, approved: bool = False, estimate_eur: float = 0.0) -> dict[str, Any]:
        if not approved:
            return {
                "ok": False,
                "error": "approval_required",
                "note_ru": "Сначала COST ESTIMATE → CEO APPROVAL.",
            }
        return {
            "ok": False,
            "error": "live_create_not_enabled",
            "note_ru": (
                "Live Toloka create остаётся за существующим /api/farm/toloka/* "
                "после явного CEO approve. Money Hunter не списывает сам."
            ),
            "estimate_eur": estimate_eur,
        }

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        return {"ok": False, "error": "not_found", "task_id": task_id}

    def get_results(self, task_id: str) -> dict[str, Any]:
        return {"ok": False, "error": "not_found", "task_id": task_id}

    def cancel_task(self, task_id: str) -> dict[str, Any]:
        return {"ok": False, "error": "not_found", "task_id": task_id}
