"""Bridge dashboard backend → repo-root swarm module."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def ensure_swarm_importable() -> Path:
    root = repo_root()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root


def build_swarm_orchestrator(
    opportunity_service: Any,
    engine_ai_service: Any,
    *,
    memory_dir: Path,
) -> Any:
    ensure_swarm_importable()
    from swarm.orchestrator import SwarmOrchestrator

    return SwarmOrchestrator(
        opportunity_service,
        engine_ai_service,
        memory_dir=memory_dir,
    )
