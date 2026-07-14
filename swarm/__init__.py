"""Swarm — distributed micro-agent combiners (Virtus Core).

Primary combiner: AI-labeling (Groq/Gemini via Engine AI Brain).
Worker flow: Trigger → Compute → Execution → Result.
"""

from swarm.labeling_worker import LabelingWorker
from swarm.orchestrator import SwarmOrchestrator
from swarm.types import BatchResult, LabelResult, LabelTask, WorkerFlowStep

__all__ = [
    "BatchResult",
    "LabelResult",
    "LabelTask",
    "LabelingWorker",
    "SwarmOrchestrator",
    "WorkerFlowStep",
]
