"""Trend Intelligence — derive patterns from observations (no fixed topic list)."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modules.tiktok_horizon.adapters.tiktok_api import TikTokOfficialAdapter
from modules.tiktok_horizon.models import TrendObservation, TrendRecord
from modules.tiktok_horizon.trend_database import TrendDatabase


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TrendIntelligence:
    """Analyzes general patterns — never copies individual videos."""

    def __init__(self, root: Path, *, tiktok: TikTokOfficialAdapter | None = None) -> None:
        self._obs_path = root / "observations.jsonl"
        self._obs_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._obs_path.exists():
            self._obs_path.write_text("", encoding="utf-8")
        self._db = TrendDatabase(root)
        self._tiktok = tiktok or TikTokOfficialAdapter(connected=False)

    @property
    def database(self) -> TrendDatabase:
        return self._db

    def ingest(self, observations: list[TrendObservation | dict[str, Any]]) -> int:
        count = 0
        with self._obs_path.open("a", encoding="utf-8") as fh:
            for raw in observations:
                if isinstance(raw, TrendObservation):
                    obs = raw
                else:
                    if not raw.get("signal_id"):
                        raw = {
                            **raw,
                            "signal_id": f"obs-{hashlib.sha1(json.dumps(raw, sort_keys=True).encode()).hexdigest()[:10]}",
                        }
                    if not raw.get("observed_at"):
                        raw = {**raw, "observed_at": _now()}
                    obs = TikTokOfficialAdapter.observation_from_dict(raw)
                if not obs.signal_id:
                    continue
                if not obs.topic_tokens:
                    continue
                fh.write(json.dumps(obs.to_dict(), ensure_ascii=False) + "\n")
                count += 1
        return count

    def list_observations(self) -> list[dict[str, Any]]:
        return _read_jsonl(self._obs_path)

    def refresh_from_adapter(self) -> dict[str, Any]:
        result = self._tiktok.fetch_trend_signals()
        ingested = 0
        if result.ok and isinstance(result.data, list) and result.data:
            ingested = self.ingest(result.data)
        trends = self.analyze_and_persist()
        return {
            "adapter": result.to_dict() if hasattr(result, "to_dict") else {
                "ok": result.ok,
                "provider": result.provider,
                "error": result.error,
                "stage1_disabled": result.stage1_disabled,
                "meta": result.meta,
            },
            "ingested_from_adapter": ingested,
            "trends_updated": len(trends),
            "trends": [t.to_dict() for t in trends],
        }

    def analyze_and_persist(self) -> list[TrendRecord]:
        """Cluster observations into emergent trend records."""
        observations = self.list_observations()
        if not observations:
            return []

        buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for obs in observations:
            tokens = [str(t).lower() for t in (obs.get("topic_tokens") or []) if t]
            if not tokens:
                continue
            # Primary key = dominant token + hook + edit style (emergent, not curated list)
            primary = Counter(tokens).most_common(1)[0][0]
            hook = str(obs.get("hook_style") or "unknown")
            edit = str(obs.get("editing_style") or "unknown")
            key = f"{primary}|{hook}|{edit}"
            buckets[key].append(obs)

        records: list[TrendRecord] = []
        for key, rows in buckets.items():
            primary, hook, edit = key.split("|", 2)
            token_counter: Counter[str] = Counter()
            tag_counter: Counter[str] = Counter()
            caption_counter: Counter[str] = Counter()
            durations: list[float] = []
            engagement = 0.0
            for row in rows:
                token_counter.update(str(t).lower() for t in (row.get("topic_tokens") or []))
                tag_counter.update(str(t) for t in (row.get("hashtag_pattern") or []))
                caption_counter[str(row.get("caption_style") or "unknown")] += 1
                durations.append(float(row.get("duration_sec") or 0))
                engagement += float(row.get("engagement_proxy") or 0)

            n = len(rows)
            avg_dur = sum(durations) / max(n, 1)
            growth = round(engagement / max(n, 1) + min(n, 10) * 0.15, 3)
            top_tokens = [t for t, _ in token_counter.most_common(5)]
            label = " / ".join(top_tokens[:3]) if top_tokens else primary
            trend_id = "tr-" + hashlib.sha1(key.encode()).hexdigest()[:12]
            existing = self._db.get(trend_id)
            detected = (existing or {}).get("detected_date") or _now()
            record = TrendRecord(
                trend_id=trend_id,
                topic_label=label[:120],
                growth_score=growth,
                average_duration=round(avg_dur, 1),
                hook_style=hook,
                editing_style=edit,
                caption_style=caption_counter.most_common(1)[0][0],
                hashtag_pattern=[t for t, _ in tag_counter.most_common(6)],
                detected_date=detected,
                last_updated=_now(),
                observation_count=n,
                sample_tokens=top_tokens,
            )
            self._db.upsert(record)
            records.append(record)

        records.sort(key=lambda r: r.growth_score, reverse=True)
        return records


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out
