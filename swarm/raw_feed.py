"""Raw feed scraper — collects labeling raw material (Trigger upstream)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def scrape_raw_from_opportunities(opportunity_service: Any, *, memory_dir: Path, limit: int = 50) -> int:
    """Micro-combiner: extract text chunks from scans into swarm_raw_queue.jsonl."""
    queue_path = memory_dir / "swarm_raw_queue.jsonl"
    rows = opportunity_service.list_opportunities(source_id="asset_scan", limit=limit * 2)
    written = 0
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as fh:
        for row in rows:
            if written >= limit:
                break
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            if meta.get("swarm_raw_queued"):
                continue
            issues = meta.get("issues") or []
            title = str(meta.get("title") or row.get("company_name") or "")
            body = " | ".join([title, *[str(i) for i in issues[:8]]]).strip()
            if len(body) < 12:
                continue
            item = {
                "id": f"raw-{uuid.uuid4().hex[:10]}",
                "source_id": "raw_feed",
                "company": row.get("company_name"),
                "url": row.get("website_url"),
                "raw_text": body[:4000],
                "context": {"opportunity_id": row.get("id")},
                "queued_at": datetime.now(timezone.utc).isoformat(),
            }
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
            meta["swarm_raw_queued"] = True
            opportunity_service.update(str(row["id"]), {"meta": meta})
            written += 1
    return written
