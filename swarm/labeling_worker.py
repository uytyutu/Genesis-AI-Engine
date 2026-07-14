"""AI-labeling combiner — Compute + Execution for training-data tags."""

from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any, Callable, Protocol

from swarm.types import LabelResult, LabelTask, WorkerFlowStep

_LABEL_PAY_EUR = 0.05

_QUALITY_KEYWORDS = {
    "positive": ("modern", "fast", "https", "mobile", "responsive"),
    "negative": ("slow", "error", "broken", "veraltet", "baustelle", "http only"),
}


class ModelClient(Protocol):
    def label_text(
        self,
        *,
        raw_text: str,
        company: str,
        url: str,
        router_task: str = "simple",
    ) -> dict[str, Any]: ...


class HeuristicModelClient:
    """Zero-cost local labeling when cloud LLM unavailable."""

    def label_text(
        self,
        *,
        raw_text: str,
        company: str,
        url: str,
        router_task: str = "simple",
    ) -> dict[str, Any]:
        blob = f"{company} {url} {raw_text}".lower()
        tags: list[str] = []
        if "https" not in blob and "http" in blob:
            tags.append("insecure_transport")
        if any(w in blob for w in ("restaurant", "cafe", "coffee", "food")):
            tags.append("hospitality")
        if any(w in blob for w in ("shop", "store", "retail", "laden")):
            tags.append("retail")
        if any(w in blob for w in ("werkstatt", "repair", "garage", "auto")):
            tags.append("automotive")
        if any(w in blob for w in ("slow", "langsame", "performance")):
            tags.append("performance_issue")
        if any(w in blob for w in ("coming soon", "under construction", "baustelle")):
            tags.append("stale_site")
        sentiment = "neutral"
        pos = sum(1 for w in _QUALITY_KEYWORDS["positive"] if w in blob)
        neg = sum(1 for w in _QUALITY_KEYWORDS["negative"] if w in blob)
        if neg > pos:
            sentiment = "needs_work"
        elif pos > neg:
            sentiment = "acceptable"
        quality = max(0.1, min(0.95, 0.5 + (pos - neg) * 0.12))
        return {
            "niche_tags": tags or ["general_business"],
            "sentiment": sentiment,
            "quality_score": round(quality, 2),
            "language_guess": "de" if any(c in blob for c in ("ä", "ö", "ü", "ß")) else "en",
            "source": "heuristic",
        }


class EngineAIModelClient:
    """Routes labeling through Genesis Engine AI Brain (Groq/Gemini)."""

    def __init__(self, engine_ai_service: Any) -> None:
        self._ai = engine_ai_service

    def label_text(
        self,
        *,
        raw_text: str,
        company: str,
        url: str,
        router_task: str = "simple",
    ) -> dict[str, Any]:
        result = self._ai.classify_niche(
            analysis={"issues": [raw_text[:500]], "title": company, "tech_stack": []},
            company=company,
            url=url,
            router_task=router_task,
        )
        tags = [str(result.get("niche") or "local_service")]
        label = str(result.get("label") or "")
        if label:
            tags.append(label.lower().replace(" ", "_")[:40])
        return {
            "niche_tags": tags,
            "sentiment": "needs_work" if "error" in raw_text.lower() else "neutral",
            "quality_score": float(result.get("confidence") or 0.7),
            "language_guess": "multi",
            "source": str(result.get("source") or "llm"),
            "provider": str(result.get("provider") or ""),
        }


class LabelingWorker:
    """AI-labeling combiner — async batch, low RAM (no browser)."""

    def __init__(
        self,
        task_source: Any,
        model_client: ModelClient | Callable[..., Any],
        *,
        priority_manager: Any | None = None,
    ) -> None:
        self.task_source = task_source
        self.model = model_client
        self.priority = priority_manager

    def _compute_labels(self, task: LabelTask, *, router_task: str = "simple") -> dict[str, Any]:
        if hasattr(self.model, "label_text"):
            return self.model.label_text(
                raw_text=task.raw_text,
                company=task.company,
                url=task.url,
                router_task=router_task,
            )
        return HeuristicModelClient().label_text(
            raw_text=task.raw_text,
            company=task.company,
            url=task.url,
            router_task=router_task,
        )

    async def process_one(self, task: LabelTask) -> LabelResult:
        flow = [WorkerFlowStep.TRIGGER.value]
        started = time.perf_counter()
        router_task = "simple"
        cached = False
        try:
            route: dict[str, Any] = {}
            if self.priority is not None:
                route = self.priority.route_label_task(task)
                router_task = str(route.get("router_task") or "simple")
                fingerprint = str(route.get("fingerprint") or "")
                hit = self.priority.cache.get(fingerprint) if fingerprint else None
                if hit:
                    flow.append(WorkerFlowStep.COMPUTE.value)
                    labels = dict(hit)
                    labels["source"] = "cache"
                    cached = True
                    llm_cost = 0.0
                    flow.append(WorkerFlowStep.EXECUTION.value)
                    await asyncio.to_thread(
                        self.task_source.submit,
                        task.id,
                        labels,
                        source_id=task.source_id,
                    )
                    flow.append(WorkerFlowStep.RESULT.value)
                    tag_preview = ", ".join(labels.get("niche_tags") or [])[:60]
                    return LabelResult(
                        task_id=task.id,
                        ok=True,
                        labels=labels,
                        confidence=float(labels.get("quality_score") or 0.7),
                        pay_eur=_LABEL_PAY_EUR,
                        llm_cost_eur=llm_cost,
                        detail=f"Кэш: {tag_preview}",
                        flow=flow,
                        duration_ms=round((time.perf_counter() - started) * 1000, 2),
                        cached=True,
                        router_task=router_task,
                    )

            flow.append(WorkerFlowStep.COMPUTE.value)
            labels = await asyncio.to_thread(
                self._compute_labels,
                task,
                router_task=router_task,
            )
            llm_cost = 0.001 if labels.get("source") in {"llm", "llm_router"} else 0.0
            if self.priority is not None and route.get("fingerprint"):
                self.priority.cache.put(str(route["fingerprint"]), labels)
            flow.append(WorkerFlowStep.EXECUTION.value)
            await asyncio.to_thread(
                self.task_source.submit,
                task.id,
                labels,
                source_id=task.source_id,
            )
            flow.append(WorkerFlowStep.RESULT.value)
            tag_preview = ", ".join(labels.get("niche_tags") or [])[:60]
            return LabelResult(
                task_id=task.id,
                ok=True,
                labels=labels,
                confidence=float(labels.get("quality_score") or 0.7),
                pay_eur=_LABEL_PAY_EUR,
                llm_cost_eur=llm_cost,
                detail=f"Теги: {tag_preview}",
                flow=flow,
                duration_ms=round((time.perf_counter() - started) * 1000, 2),
                cached=cached,
                router_task=router_task,
            )
        except Exception as exc:
            return LabelResult(
                task_id=task.id,
                ok=False,
                labels={},
                confidence=0.0,
                pay_eur=0.0,
                detail=str(exc)[:120],
                flow=flow,
                duration_ms=round((time.perf_counter() - started) * 1000, 2),
                router_task=router_task,
            )

    async def process_batch(self, limit: int = 10, *, concurrency: int = 20) -> list[LabelResult]:
        tasks = await asyncio.to_thread(self.task_source.pull, limit)
        if not tasks:
            return []
        sem = asyncio.Semaphore(max(1, min(concurrency, limit)))
        results: list[LabelResult] = []

        async def _guarded(task: LabelTask) -> LabelResult:
            async with sem:
                return await self.process_one(task)

        gathered = await asyncio.gather(*[_guarded(t) for t in tasks], return_exceptions=True)
        for item in gathered:
            if isinstance(item, LabelResult):
                results.append(item)
            elif isinstance(item, Exception):
                results.append(
                    LabelResult(
                        task_id="error",
                        ok=False,
                        labels={},
                        confidence=0.0,
                        pay_eur=0.0,
                        detail=str(item)[:120],
                    )
                )
        return results
