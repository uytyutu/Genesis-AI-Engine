"""Priority Manager — complexity routing, model tier, and knowledge cache for the swarm."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from swarm.adaptive_arbitrage import AdaptiveArbitrage
from swarm.cloud_dispatcher import CloudDispatcher
from swarm.farm_learning import FarmLearningLedger
from swarm.node_monitor import NodeMonitor
from swarm.types import LabelTask

_SIMPLE_ROUTER_TASK = "simple"
_COMPLEX_ROUTER_TASK = "document_analysis"
_FLASH_TIER = "flash"
_PRO_TIER = "pro"


def estimate_complexity(*, adapter_id: str, raw_text: str = "", meta: dict[str, Any] | None = None) -> str:
    """Heuristic complexity — no extra LLM call."""
    blob = raw_text or ""
    if meta:
        issues = meta.get("issues") or []
        if isinstance(issues, list):
            blob += " " + " ".join(str(i) for i in issues[:8])
    length = len(blob.strip())
    if adapter_id in {"record_verify", "data_clean"} or length < 180:
        return "simple"
    if length > 900 or adapter_id == "text_classify":
        return "complex"
    return "medium"


def route_for_task(*, complexity: str, adapter_id: str = "ai_labeling") -> dict[str, Any]:
    """Map task → LLM Router task + model tier (Flash vs Pro path)."""
    if complexity == "complex" or adapter_id == "text_classify":
        return {
            "complexity": complexity,
            "adapter_id": adapter_id,
            "router_task": _COMPLEX_ROUTER_TASK,
            "capability": "analysis",
            "model_tier": _PRO_TIER,
            "premium_allowed": False,
        }
    if complexity == "medium":
        return {
            "complexity": complexity,
            "adapter_id": adapter_id,
            "router_task": "conversation",
            "capability": "conversation",
            "model_tier": _FLASH_TIER,
            "premium_allowed": False,
        }
    return {
        "complexity": complexity,
        "adapter_id": adapter_id,
        "router_task": _SIMPLE_ROUTER_TASK,
        "capability": "conversation",
        "model_tier": _FLASH_TIER,
        "premium_allowed": False,
    }


class KnowledgeCache:
    """Lightweight pattern cache — avoids repeat LLM calls for similar labeling input."""

    def __init__(self, memory_dir: Path, *, max_entries: int = 500) -> None:
        self._path = Path(memory_dir) / "micro_farm_label_cache.json"
        self._max = max_entries

    def _load(self) -> dict[str, Any]:
        if not self._path.is_file():
            return {"entries": {}}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"entries": {}}

    def _save(self, data: dict[str, Any]) -> None:
        entries = data.get("entries") or {}
        if len(entries) > self._max:
            # Drop oldest half — simple LRU by insertion order in py3.7+ dicts preserve order
            keys = list(entries.keys())
            for key in keys[: len(keys) // 2]:
                entries.pop(key, None)
        data["entries"] = entries
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def fingerprint(*, raw_text: str, company: str = "", url: str = "") -> str:
        norm = re.sub(r"\s+", " ", f"{company}|{url}|{raw_text[:320]}").strip().lower()
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:20]

    def get(self, fingerprint: str) -> dict[str, Any] | None:
        entry = (self._load().get("entries") or {}).get(fingerprint)
        if isinstance(entry, dict) and entry.get("labels"):
            return dict(entry["labels"])
        return None

    def put(self, fingerprint: str, labels: dict[str, Any]) -> None:
        data = self._load()
        entries = data.setdefault("entries", {})
        entries[fingerprint] = {"labels": labels}
        self._save(data)

    def stats(self) -> dict[str, Any]:
        entries = (self._load().get("entries") or {})
        return {"entries": len(entries), "max_entries": self._max}


class PriorityManager:
    """Plans routes, cache lookups, and batch ordering for the micro-farm."""

    def __init__(self, memory_dir: Path, *, env_getter: Any | None = None) -> None:
        self._memory = Path(memory_dir)
        self.cache = KnowledgeCache(self._memory)
        self.learning = FarmLearningLedger(self._memory)
        self.dispatcher = CloudDispatcher(env_getter=env_getter)
        self.nodes = NodeMonitor(self._memory, env_getter=env_getter)
        self.arbitrage = AdaptiveArbitrage()

    def route_label_task(self, task: LabelTask) -> dict[str, Any]:
        complexity = estimate_complexity(
            adapter_id="ai_labeling",
            raw_text=task.raw_text,
            meta=task.context if isinstance(task.context, dict) else None,
        )
        route = route_for_task(complexity=complexity, adapter_id="ai_labeling")
        route["fingerprint"] = self.cache.fingerprint(
            raw_text=task.raw_text,
            company=task.company,
            url=task.url,
        )
        route["execution"] = self.dispatcher.resolve_execution(adapter_id="ai_labeling", profitable=True)
        return route

    def route_legacy(self, *, adapter_id: str, raw_text: str = "", meta: dict[str, Any] | None = None) -> dict[str, Any]:
        complexity = estimate_complexity(adapter_id=adapter_id, raw_text=raw_text, meta=meta)
        route = route_for_task(complexity=complexity, adapter_id=adapter_id)
        route["execution"] = self.dispatcher.resolve_execution(adapter_id=adapter_id, profitable=True)
        return route

    def allocate_workers(self, total: int, combiner_ids: tuple[str, ...]) -> dict[str, int]:
        """Split batch slots by learned ROI when investor_mode is on."""
        total = max(1, int(total))
        order = self.learning.recommend_order(combiner_ids)
        if not self.learning.ready():
            primary = combiner_ids[0] if combiner_ids else "ai_labeling"
            return {primary: total}
        weights = list(range(len(order), 0, -1))
        weight_sum = sum(weights) or 1
        alloc: dict[str, int] = {}
        remaining = total
        for idx, adapter_id in enumerate(order):
            if idx == len(order) - 1:
                slots = remaining
            else:
                slots = max(1, int(total * weights[idx] / weight_sum))
                remaining -= slots
            alloc[adapter_id] = alloc.get(adapter_id, 0) + max(0, slots)
        return alloc

    def arbitrage_decision(self) -> dict[str, Any]:
        node_snap = self.nodes.snapshot()
        return self.arbitrage.decide(
            self.learning,
            node_eur_per_day=float(node_snap.get("projected_eur_per_day") or 0),
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "pipeline_parallelism": True,
            "async_note": "Рой уже шлёт пакеты в LLM параллельно (asyncio + semaphore)",
            "cache": self.cache.stats(),
            "learning": self.learning.snapshot(),
            "router_note": "Простые задачи → Flash (Groq/Gemini), сложные → analysis tier",
            "cloud_dispatcher": self.dispatcher.snapshot(),
            "node_monitor": self.nodes.snapshot(),
            "adaptive_arbitrage": self.arbitrage_decision(),
        }
