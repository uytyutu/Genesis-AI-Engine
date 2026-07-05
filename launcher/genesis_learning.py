"""Genesis Learning — project knowledge from resolved bugs (Detect → Remember, not auto-fix)."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from launcher import paths

CYCLE = ("Detect", "Analyze", "Recommend", "Approve", "Fix", "Verify", "Remember")


@dataclass
class LearningIncident:
    id: str
    symptom: str
    root_cause: str
    fix: str
    files: list[str]
    date: str
    version: str
    verify: str
    regression: str
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _kb_path(root: Path | None = None) -> Path:
    return paths.memory_dir(root) / "genesis_learning.json"


def load_kb(root: Path | None = None) -> dict[str, Any]:
    path = _kb_path(root)
    if not path.is_file():
        _seed_kb_if_needed(root)
    if not path.is_file():
        return {"version": 1, "incidents": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "incidents": []}


def _seed_kb_if_needed(root: Path | None = None) -> None:
    root = root or paths.find_project_root()
    seed = root / "dashboard" / "backend" / "app" / "memory" / "genesis_learning_incidents_seed.json"
    if not seed.is_file():
        return
    try:
        items = json.loads(seed.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    save_kb({"version": 1, "incidents": items, "seeded_from": str(seed)}, root)


def save_kb(data: dict[str, Any], root: Path | None = None) -> None:
    path = _kb_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def find_similar(symptom: str, root: Path | None = None) -> list[dict[str, Any]]:
    """Return past incidents matching symptom text — for faster analysis, not auto-fix."""
    kb = load_kb(root)
    needle = symptom.lower()
    hits: list[dict[str, Any]] = []
    for item in kb.get("incidents", []):
        blob = " ".join(
            str(item.get(k, "")) for k in ("symptom", "root_cause", "fix", "tags")
        ).lower()
        if needle in blob or any(t in needle for t in item.get("tags", [])):
            hits.append(item)
    return hits


def record_incident(incident: LearningIncident, root: Path | None = None) -> None:
    kb = load_kb(root)
    incidents: list[dict[str, Any]] = kb.setdefault("incidents", [])
    incidents = [i for i in incidents if i.get("id") != incident.id]
    incidents.insert(0, incident.to_dict())
    kb["incidents"] = incidents[:200]
    kb["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_kb(kb, root)


def record_from_error(exc: BaseException, *, fix: str, files: list[str], verify: str, regression: str) -> None:
    """Convenience after a verified fix."""
    msg = str(exc)
    slug = re.sub(r"[^a-z0-9]+", "-", msg.lower())[:48].strip("-") or "error"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    record_incident(
        LearningIncident(
            id=f"{today}-{slug}",
            symptom="Не удалось запустить Genesis" if "CTkImage" in msg else msg[:120],
            root_cause=msg,
            fix=fix,
            files=files,
            date=today,
            version="0.5.0",
            verify=verify,
            regression=regression,
            tags=["launcher", "startup"],
        )
    )
