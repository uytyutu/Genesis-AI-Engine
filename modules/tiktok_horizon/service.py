"""HorizonService — Stage 1 orchestrator (owner-only, kill-switched)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modules.tiktok_horizon.adapters.tiktok_api import TikTokOfficialAdapter
from modules.tiktok_horizon.adapters.tts_api import TtsAdapter
from modules.tiktok_horizon.adapters.video_api import VideoGeneratorAdapter
from modules.tiktok_horizon.analytics import AnalyticsStore
from modules.tiktok_horizon.content_quality import ContentQualityEngine
from modules.tiktok_horizon.gate import is_horizon_enabled, require_horizon_enabled
from modules.tiktok_horizon.human_review import HumanReviewEngine
from modules.tiktok_horizon.idea_generator import IdeaGenerator
from modules.tiktok_horizon.learning_engine import LearningEngine
from modules.tiktok_horizon.prompt_builder import PromptBuilder
from modules.tiktok_horizon.publish_intelligence import PublishIntelligence
from modules.tiktok_horizon.scheduler import Scheduler
from modules.tiktok_horizon.script_generator import ScriptGenerator
from modules.tiktok_horizon.trend_intelligence import TrendIntelligence

STAGE1_CAPABILITIES = {
    "trend_intelligence": True,
    "trend_database": True,
    "idea_generator": True,
    "script_generator": True,
    "prompt_builder": True,
    "content_quality": True,
    "human_review": True,
    "publish_intelligence": True,
    "scheduler_queue": True,
    "analytics_schema": True,
    "learning_architecture": True,
    "tiktok_adapter_stub": True,
    "video_generation": False,
    "tts_generation": False,
    "auto_publish": False,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HorizonService:
    def __init__(self, memory_dir: Path) -> None:
        self._root = memory_dir / "tiktok_horizon"
        self._root.mkdir(parents=True, exist_ok=True)
        self._drafts = self._root / "drafts.jsonl"
        if not self._drafts.exists():
            self._drafts.write_text("", encoding="utf-8")

        self.tiktok = TikTokOfficialAdapter(connected=False)
        self.video = VideoGeneratorAdapter()
        self.tts = TtsAdapter()
        self.trends = TrendIntelligence(self._root, tiktok=self.tiktok)
        self.ideas = IdeaGenerator()
        self.scripts = ScriptGenerator()
        self.prompts = PromptBuilder()
        self.quality = ContentQualityEngine()
        self.review = HumanReviewEngine()
        self.publish_intel = PublishIntelligence()
        self.scheduler = Scheduler(self._root)
        self.analytics = AnalyticsStore(self._root)
        self.learning = LearningEngine(self._root)

    def _require(self) -> None:
        try:
            require_horizon_enabled()
        except RuntimeError as exc:
            raise ValueError("tiktok_disabled") from exc

    def dashboard(self) -> dict[str, Any]:
        enabled = is_horizon_enabled()
        drafts = self.list_drafts()
        return {
            "ok": True,
            "module": "tiktok_horizon",
            "stage": 1,
            "tiktok_enabled": enabled,
            "capabilities": STAGE1_CAPABILITIES,
            "counts": {
                "observations": len(self.trends.list_observations()),
                "trends": len(self.trends.database.list_all()),
                "drafts": len(drafts),
                "review": sum(1 for d in drafts if d.get("status") == "review"),
                "approved": sum(1 for d in drafts if d.get("status") == "approved"),
                "queue": len(self.scheduler.list_queue()),
            },
            "adapters": {
                "tiktok": self.tiktok.health().__dict__,
                "video": self.video.health().__dict__,
                "tts": self.tts.health().__dict__,
            },
            "learning": self.learning.summary(),
            "analytics_schema": self.analytics.schema(),
            "pipeline_ru": "Trend → Draft → Human Review → Approve → Queue (publish OFF)",
            "note_ru": (
                "Внутренний модуль владельца. Не клиентский сервис. "
                "Генерация видео и публикация отключены на Stage 1."
            ),
        }

    def ingest_observations(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        self._require()
        n = self.trends.ingest(rows)
        trends = self.trends.analyze_and_persist()
        return {
            "ok": True,
            "ingested": n,
            "trends": [t.to_dict() for t in trends],
        }

    def refresh_trends(self) -> dict[str, Any]:
        self._require()
        return self.trends.refresh_from_adapter()

    def list_trends(self) -> list[dict[str, Any]]:
        return self.trends.database.top_by_growth(50)

    def list_drafts(self) -> list[dict[str, Any]]:
        rows = _read_jsonl(self._drafts)
        rows.sort(key=lambda r: r.get("updated_at") or r.get("created_at") or "", reverse=True)
        return rows

    def get_draft(self, draft_id: str) -> dict[str, Any] | None:
        for row in self.list_drafts():
            if row.get("id") == draft_id:
                return row
        return None

    def generate_drafts(
        self,
        *,
        limit: int = 3,
        language: str = "ru",
    ) -> list[dict[str, Any]]:
        self._require()
        trends = self.trends.database.top_by_growth(limit * 2)
        if not trends:
            # Re-analyze from observations if DB empty
            self.trends.analyze_and_persist()
            trends = self.trends.database.top_by_growth(limit * 2)
        if not trends:
            raise ValueError("no_trends")

        recent_styles = [
            str((d.get("script") or {}).get("style_variant") or "")
            for d in self.list_drafts()[:10]
        ]
        ideas = self.ideas.generate_from_trends(trends, limit=limit, language=language)
        created: list[dict[str, Any]] = []
        for idea in ideas:
            trend = next((t for t in trends if t.get("trend_id") == idea.trend_id), None)
            script = self.scripts.build(idea, trend=trend, language=language)
            avg_dur = int(float((trend or {}).get("average_duration") or 25))
            prompt = self.prompts.build(script, duration_sec=avg_dur)
            quality = self.quality.score(
                script=script,
                idea=idea.to_dict(),
                recent_styles=recent_styles,
            )
            window = self.publish_intel.recommend(
                draft={"style_variant": idea.style_variant, "script": script.to_dict()},
                analytics_rows=self.analytics.list_rows(),
            )
            row = {
                "id": f"hz-{uuid.uuid4().hex[:10]}",
                "status": "review",
                "created_at": _now(),
                "updated_at": _now(),
                "title": idea.title,
                "style_variant": idea.style_variant,
                "idea": idea.to_dict(),
                "script": script.to_dict(),
                "prompt": prompt.to_dict(),
                "quality": quality.to_dict(),
                "quality_ready": quality.ready,
                "publish_window": window.to_dict(),
                "voice_preference": "default",
                "subtitles_enabled": True,
                "scene_order": list(script.structure),
                "human_edited": False,
                "video_generation": False,
                "publish_enabled": False,
            }
            _append_jsonl(self._drafts, row)
            recent_styles.append(idea.style_variant)
            created.append(row)
            self.learning.record_event(
                {
                    "event_type": "draft_generated",
                    "draft_id": row["id"],
                    "payload": {"style": idea.style_variant, "trend_id": idea.trend_id},
                }
            )
        return created

    def review_checklist(self, draft_id: str) -> dict[str, Any]:
        self._require()
        draft = self.get_draft(draft_id)
        if not draft:
            raise ValueError("draft_not_found")
        return self.review.checklist(draft)

    def apply_review_edits(self, draft_id: str, edits: dict[str, Any]) -> dict[str, Any]:
        self._require()
        draft = self.get_draft(draft_id)
        if not draft:
            raise ValueError("draft_not_found")
        updated = self.review.apply_edits(draft, edits or {})
        # Re-score after human edits
        quality = self.quality.score(
            script=updated.get("script") or {},
            idea=updated.get("idea"),
            recent_styles=[],
        )
        updated["quality"] = quality.to_dict()
        updated["quality_ready"] = quality.ready
        updated["updated_at"] = _now()
        self._rewrite_draft(updated)
        self.learning.record_event(
            {
                "event_type": "human_edit",
                "draft_id": draft_id,
                "payload": {"fields": sorted((edits or {}).keys())},
            }
        )
        return updated

    def approve_draft(self, draft_id: str) -> dict[str, Any]:
        self._require()
        draft = self.get_draft(draft_id)
        if not draft:
            raise ValueError("draft_not_found")
        draft = dict(draft)
        draft["status"] = "approved"
        draft["approved_at"] = _now()
        draft["updated_at"] = _now()
        self._rewrite_draft(draft)
        self.learning.record_event(
            {"event_type": "approved", "draft_id": draft_id, "payload": {}}
        )
        return draft

    def enqueue_draft(self, draft_id: str) -> dict[str, Any]:
        self._require()
        draft = self.get_draft(draft_id)
        if not draft:
            raise ValueError("draft_not_found")
        item = self.scheduler.enqueue(draft)
        draft = dict(draft)
        draft["status"] = "queued"
        draft["updated_at"] = _now()
        self._rewrite_draft(draft)
        return item

    def list_queue(self) -> list[dict[str, Any]]:
        return self.scheduler.list_queue()

    def _rewrite_draft(self, draft: dict[str, Any]) -> None:
        rows = self.list_drafts()
        out = []
        found = False
        for row in rows:
            if row.get("id") == draft.get("id"):
                out.append(draft)
                found = True
            else:
                out.append(row)
        if not found:
            out.append(draft)
        with self._drafts.open("w", encoding="utf-8") as fh:
            for row in out:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")


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


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
