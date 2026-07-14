"""Task sources — where combiners pull raw data (Trigger phase)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from swarm.types import LabelTask


class TaskSource(Protocol):
    def pull(self, limit: int) -> list[LabelTask]: ...
    def submit(self, task_id: str, labels: dict[str, Any], *, source_id: str) -> None: ...


class InternalOpportunitySource:
    """Pull unlabeled text from Genesis asset_scan opportunities (open internal feed)."""

    def __init__(
        self,
        opportunity_service: Any,
        *,
        memory_dir: Path,
    ) -> None:
        self._opportunity = opportunity_service
        self._memory = memory_dir
        self._export_path = memory_dir / "swarm_labels_export.jsonl"

    def pull(self, limit: int) -> list[LabelTask]:
        rows = self._opportunity.list_opportunities(source_id="asset_scan", limit=limit * 6)
        out: list[LabelTask] = []
        for row in rows:
            if len(out) >= limit:
                break
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            if meta.get("swarm_labeled"):
                continue
            issues = meta.get("issues") or meta.get("site_issues") or []
            title = str(meta.get("title") or row.get("company_name") or "")
            tech = meta.get("tech_stack") or []
            chunks = [title, *issues, *[str(t) for t in tech[:5]]]
            raw = " | ".join(c for c in chunks if c).strip()
            if len(raw) < 8:
                continue
            out.append(
                LabelTask(
                    id=str(row["id"]),
                    source_id="asset_scan",
                    raw_text=raw[:4000],
                    company=str(row.get("company_name") or ""),
                    url=str(row.get("website_url") or ""),
                    context={"meta": meta},
                )
            )
        return out

    def submit(self, task_id: str, labels: dict[str, Any], *, source_id: str) -> None:
        row = self._opportunity.get(task_id)
        if not row:
            return
        meta = dict(row.get("meta") or {})
        meta["swarm_labeled"] = True
        meta["swarm_labels"] = labels
        meta["swarm_labeled_at"] = datetime.now(timezone.utc).isoformat()
        self._opportunity.update(task_id, {"meta": meta})
        self._export_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "task_id": task_id,
            "source_id": source_id,
            "labels": labels,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._export_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


class RawQueueSource:
    """JSONL queue written by raw_feed scraper — fallback when opportunities empty."""

    def __init__(self, memory_dir: Path) -> None:
        self._path = memory_dir / "swarm_raw_queue.jsonl"
        self._done_path = memory_dir / "swarm_raw_done.jsonl"
        self._memory = memory_dir

    def pull(self, limit: int) -> list[LabelTask]:
        if not self._path.is_file():
            return []
        done_ids = set()
        if self._done_path.is_file():
            for line in self._done_path.read_text(encoding="utf-8").splitlines():
                try:
                    done_ids.add(json.loads(line).get("id"))
                except json.JSONDecodeError:
                    continue
        out: list[LabelTask] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if len(out) >= limit:
                break
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            tid = str(data.get("id") or "")
            if not tid or tid in done_ids:
                continue
            raw = str(data.get("raw_text") or "").strip()
            if len(raw) < 8:
                continue
            out.append(
                LabelTask(
                    id=tid,
                    source_id=str(data.get("source_id") or "raw_queue"),
                    raw_text=raw[:4000],
                    company=str(data.get("company") or ""),
                    url=str(data.get("url") or ""),
                    context=data.get("context") if isinstance(data.get("context"), dict) else {},
                )
            )
        return out

    def submit(self, task_id: str, labels: dict[str, Any], *, source_id: str) -> None:
        self._done_path.parent.mkdir(parents=True, exist_ok=True)
        with self._done_path.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "id": task_id,
                        "source_id": source_id,
                        "labels": labels,
                        "at": datetime.now(timezone.utc).isoformat(),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        export = self._memory / "swarm_labels_export.jsonl"
        with export.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {"task_id": task_id, "source_id": source_id, "labels": labels},
                    ensure_ascii=False,
                )
                + "\n"
            )


class CompositeTaskSource:
    """Opportunities first, then raw queue — maximizes Trigger coverage."""

    def __init__(self, *sources: TaskSource) -> None:
        self._sources = sources

    def pull(self, limit: int) -> list[LabelTask]:
        out: list[LabelTask] = []
        for src in self._sources:
            need = limit - len(out)
            if need <= 0:
                break
            out.extend(src.pull(need))
        return out[:limit]

    def submit(self, task_id: str, labels: dict[str, Any], *, source_id: str) -> None:
        for src in self._sources:
            try:
                src.submit(task_id, labels, source_id=source_id)
            except Exception:
                continue
