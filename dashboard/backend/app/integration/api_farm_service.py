"""Thin façade: Mission Control ↔ swarm.farm_channels.rapidapi."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from swarm.farm_channels.rapidapi.monitor import (
    pause_candidate,
    portfolio_metrics,
    resume_candidate,
)
from swarm.farm_channels.rapidapi.publisher import approve_candidate, publish_candidate
from swarm.farm_channels.rapidapi.quality_gate import run_quality_gate
from swarm.farm_channels.rapidapi.builder import build_candidate
from swarm.farm_channels.rapidapi.research import discover_candidates, research_refresh
from swarm.farm_channels.rapidapi.revenue import ingest_revenue_event, revenue_summary
from swarm.farm_channels.rapidapi.scoring import rank_candidates, score_candidate
from swarm.farm_channels.rapidapi.select import select_best_candidate
from swarm.farm_channels.rapidapi.store import ApiFarmStore
from swarm.farm_channels.rapidapi.worker import (
    enqueue_pipeline,
    run_burst,
    run_first_api,
    status_payload,
    step,
)


class ApiFarmService:
    def __init__(self, memory_dir: Path | None = None) -> None:
        self._store = ApiFarmStore(memory_dir)

    def status(self) -> dict[str, Any]:
        return status_payload(self._store)

    def candidates(self, *, top: int = 50) -> dict[str, Any]:
        rows = self._store.list_candidates()
        ranked = rank_candidates(rows, top_n=max(1, int(top)))
        best = select_best_candidate(self._store)
        return {
            "ok": True,
            "count": len(rows),
            "candidates": ranked,
            "top5": ranked[:5],
            "best": best,
            "portfolio": portfolio_metrics(self._store),
        }

    def jobs(self, *, limit: int = 100) -> dict[str, Any]:
        return {"ok": True, "jobs": self._store.list_jobs(limit=limit)}

    def revenue(self) -> dict[str, Any]:
        return {
            "ok": True,
            "summary": revenue_summary(self._store),
            "events": self._store.list_revenue_events(limit=100),
        }

    def run(
        self,
        *,
        action: str = "discover",
        candidate_id: str = "",
        max_steps: int = 8,
    ) -> dict[str, Any]:
        action = (action or "discover").strip().lower()
        if action in ("first_api", "first-api", "first"):
            return run_first_api(self._store, max_steps=max_steps)
        if action == "discover":
            created = discover_candidates(self._store, limit=10)
            best = select_best_candidate(self._store)
            if best:
                enqueue_pipeline(
                    self._store,
                    discover=False,
                    candidate_id=str(best["id"]),
                    through_quality_gate=True,
                )
            burst = run_burst(self._store, max_steps=max_steps)
            return {
                "ok": True,
                "action": action,
                "created": created,
                "best": best,
                "burst": burst,
                "status": self.status(),
            }
        if action == "tick":
            return step(self._store)
        if action == "burst":
            return run_burst(self._store, max_steps=max_steps)
        if action == "acquire":
            if not candidate_id:
                return {"ok": False, "error": "candidate_id_required"}
            from swarm.farm_channels.rapidapi.acquisition import run_acquisition

            return run_acquisition(self._store, candidate_id)
        if not candidate_id:
            return {"ok": False, "error": "candidate_id_required"}
        if action == "research":
            return {"ok": True, "candidate": research_refresh(self._store, candidate_id)}
        if action == "score":
            row = self._store.get_candidate(candidate_id)
            if not row:
                return {"ok": False, "error": "candidate_not_found"}
            scored = score_candidate(row)
            return {
                "ok": True,
                "candidate": self._store.update_candidate(candidate_id, **scored),
            }
        if action == "build":
            return build_candidate(self._store, candidate_id)
        if action == "test":
            return build_candidate(self._store, candidate_id)
        if action in ("quality_gate", "quality"):
            return run_quality_gate(self._store, candidate_id)
        if action == "monitor":
            from swarm.farm_channels.rapidapi.monitor import monitor_candidate

            return monitor_candidate(self._store, candidate_id)
        if action == "pause":
            return pause_candidate(self._store, candidate_id)
        if action == "resume":
            return resume_candidate(self._store, candidate_id)
        if action == "enqueue":
            jobs = enqueue_pipeline(
                self._store,
                discover=False,
                candidate_id=candidate_id,
                through_quality_gate=True,
            )
            return {"ok": True, "jobs": jobs}
        return {"ok": False, "error": f"unknown_action:{action}"}

    def approve(self, candidate_id: str, *, note: str = "") -> dict[str, Any]:
        return approve_candidate(self._store, candidate_id, note=note)

    def publish(self, candidate_id: str) -> dict[str, Any]:
        return publish_candidate(self._store, candidate_id)

    def ingest_revenue(self, payload: dict[str, Any]) -> dict[str, Any]:
        return ingest_revenue_event(self._store, payload, memory_dir=self._store.memory_dir)

    def autonomous_tick(self, *, max_steps: int = 2) -> dict[str, Any]:
        """Called from Farm AUTO-RUN — never publishes without CEO approval."""
        if not self._store.list_candidates():
            self._store.enqueue_job("discover")
        return run_burst(self._store, max_steps=max_steps)
