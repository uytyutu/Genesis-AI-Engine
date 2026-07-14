"""Swarm orchestrator — async parallel workers (The Swarm)."""

from __future__ import annotations

import asyncio
from typing import Any

from swarm.labeling_worker import EngineAIModelClient, HeuristicModelClient, LabelingWorker
from swarm.priority_manager import PriorityManager
from swarm.raw_feed import scrape_raw_from_opportunities
from swarm.task_source import CompositeTaskSource, InternalOpportunitySource, RawQueueSource
from swarm.types import BatchResult


class SwarmOrchestrator:
    """Manages labeling swarm — hundreds of concurrent micro-tasks, minimal RAM."""

    def __init__(
        self,
        opportunity_service: Any,
        engine_ai_service: Any,
        *,
        memory_dir: Any,
    ) -> None:
        self._memory = memory_dir
        self._opportunity = opportunity_service
        self._ai = engine_ai_service
        self._priority = PriorityManager(memory_dir)
        opp_src = InternalOpportunitySource(opportunity_service, memory_dir=memory_dir)
        raw_src = RawQueueSource(memory_dir)
        self._source = CompositeTaskSource(opp_src, raw_src)
        model = EngineAIModelClient(engine_ai_service)
        self._worker = LabelingWorker(self._source, model, priority_manager=self._priority)
        self._fallback = LabelingWorker(self._source, HeuristicModelClient(), priority_manager=self._priority)

    def priority_manager(self) -> PriorityManager:
        return self._priority

    def feed_raw(self, limit: int = 40) -> int:
        return scrape_raw_from_opportunities(
            self._opportunity,
            memory_dir=self._memory,
            limit=limit,
        )

    async def run_labeling_swarm_async(
        self,
        *,
        workers: int = 10,
        concurrency: int = 50,
    ) -> BatchResult:
        self.feed_raw(min(workers, 40))
        results = await self._worker.process_batch(
            limit=max(1, min(200, workers)),
            concurrency=max(1, min(200, concurrency)),
        )
        if not results:
            results = await self._fallback.process_batch(
                limit=max(1, min(200, workers)),
                concurrency=concurrency,
            )
        done = sum(1 for r in results if r.ok)
        earned = round(sum(r.pay_eur for r in results if r.ok), 4)
        llm_cost = round(sum(r.llm_cost_eur for r in results if r.ok), 4)
        return BatchResult(
            tasks_done=done,
            earned_eur=earned,
            llm_cost_eur=llm_cost,
            results=results,
            message=(
                f"Рой: {done} разметок · +{earned:.2f} €"
                if done
                else "Нет сырья — запустите поиск сайтов (feed)"
            ),
        )

    def run_labeling_swarm(self, *, workers: int = 10, concurrency: int = 50) -> BatchResult:
        """Sync entry for FastAPI — one asyncio.run per tick."""
        return asyncio.run(
            self.run_labeling_swarm_async(workers=workers, concurrency=concurrency)
        )
