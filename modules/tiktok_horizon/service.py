"""HorizonService — Stage 1 orchestrator (owner-only, kill-switched)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modules.tiktok_horizon.adapters.tiktok_api import TikTokOfficialAdapter
from modules.tiktok_horizon.adapters.tiktok_oauth import TikTokOAuthAdapter
from modules.tiktok_horizon.adapters.tts_api import TtsAdapter
from modules.tiktok_horizon.adapters.video_api import VideoGeneratorAdapter
from modules.tiktok_horizon.accounts import TikTokAccountStore
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
from modules.tiktok_horizon.visibility import assert_owner_internal_access, visibility_policy

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
    "tiktok_oauth": True,
    "multi_account": True,
    "video_generation": False,
    "tts_generation": False,
    "auto_publish": False,
    "video_publish": False,
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

        self.accounts = TikTokAccountStore(self._root)
        self.oauth = TikTokOAuthAdapter()
        n_connected = self.accounts.connected_count()
        self.tiktok = TikTokOfficialAdapter(
            connected=n_connected > 0,
            connected_accounts=n_connected,
        )
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

    def _require_owner_module(self) -> None:
        try:
            assert_owner_internal_access()
        except RuntimeError as exc:
            raise ValueError("horizon_not_internal_owner") from exc

    def _require(self) -> None:
        self._require_owner_module()
        try:
            require_horizon_enabled()
        except RuntimeError as exc:
            raise ValueError("tiktok_disabled") from exc

    def dashboard(self) -> dict[str, Any]:
        self._require_owner_module()
        enabled = is_horizon_enabled()
        drafts = self.list_drafts()
        accounts = self.list_accounts()
        n_connected = sum(1 for a in accounts if a.get("status") == "connected")
        self.tiktok = TikTokOfficialAdapter(
            connected=n_connected > 0,
            connected_accounts=n_connected,
        )
        return {
            "ok": True,
            "module": "tiktok_horizon",
            "stage": 2,
            "tiktok_enabled": enabled,
            "visibility": visibility_policy(),
            "capabilities": STAGE1_CAPABILITIES,
            "counts": {
                "observations": len(self.trends.list_observations()),
                "trends": len(self.trends.database.list_all()),
                "drafts": len(drafts),
                "review": sum(1 for d in drafts if d.get("status") == "review"),
                "approved": sum(1 for d in drafts if d.get("status") == "approved"),
                "queue": len(self.scheduler.list_queue()),
                "accounts": len(accounts),
                "accounts_connected": n_connected,
            },
            "accounts": accounts,
            "oauth": self.oauth.health().__dict__,
            "adapters": {
                "tiktok": self.tiktok.health().__dict__,
                "tiktok_oauth": self.oauth.health().__dict__,
                "video": self.video.health().__dict__,
                "tts": self.tts.health().__dict__,
            },
            "learning": self.learning.summary(),
            "analytics_schema": self.analytics.schema(),
            "pipeline_ru": "Trend → Draft → Human Review → Approve → Queue (publish OFF)",
            "note_ru": (
                "Внутренний модуль Owner (INTERNAL_OWNER). "
                "Stage 2: OAuth мультиаккаунты. Генерация видео и публикация отключены."
            ),
        }

    # --- Stage 2: TikTok Accounts (OAuth) — no kill switch required ---

    def list_accounts(self) -> list[dict[str, Any]]:
        self._require_owner_module()
        return self.accounts.list_public()

    def oauth_status(self, *, public_api_base: str = "") -> dict[str, Any]:
        self._require_owner_module()
        redirect = (
            self.oauth.default_redirect_uri(public_api_base) if public_api_base else None
        )
        return {
            "oauth_client_ready": self.oauth.oauth_client_ready(),
            "redirect_uri": redirect,
            "scopes": (self.oauth.health().data or {}).get("scopes"),
            "accounts": self.list_accounts(),
            "multi_account": True,
            "publish_enabled": False,
            "env_required": ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET"],
            "note_ru": (
                "Зарегистрируйте redirect_uri в TikTok for Developers → Login Kit. "
                "Токены хранятся только в зашифрованном виде."
            ),
        }

    def begin_oauth(self, *, public_api_base: str) -> dict[str, Any]:
        self._require_owner_module()
        if not self.oauth.oauth_client_ready():
            raise ValueError("tiktok_oauth_not_configured")
        redirect_uri = self.oauth.default_redirect_uri(public_api_base)
        state = self.oauth.create_state()
        url = self.oauth.authorization_url(redirect_uri=redirect_uri, state=state)
        return {"authorize_url": url, "redirect_uri": redirect_uri, "state": state}

    def complete_oauth(self, *, code: str, state: str, public_api_base: str) -> dict[str, Any]:
        self._require_owner_module()
        if not self.oauth.consume_state(state):
            raise ValueError("invalid_oauth_state")
        redirect_uri = self.oauth.default_redirect_uri(public_api_base)
        tokens = self.oauth.exchange_code(code=code, redirect_uri=redirect_uri)
        if not tokens.get("ok"):
            raise ValueError(str(tokens.get("reason") or "oauth_exchange_failed"))
        profile = self.oauth.fetch_user_profile(access_token=str(tokens["access_token"]))
        display_name = profile.get("display_name") if profile.get("ok") else None
        username = profile.get("username") if profile.get("ok") else None
        avatar_url = profile.get("avatar_url") if profile.get("ok") else None
        open_id = str(tokens["open_id"])
        if profile.get("ok") and profile.get("open_id"):
            open_id = str(profile["open_id"])
        account = self.accounts.upsert_from_oauth(
            open_id=open_id,
            access_token=str(tokens["access_token"]),
            refresh_token=str(tokens.get("refresh_token") or ""),
            expires_in=int(tokens.get("expires_in") or 86400),
            refresh_expires_in=int(tokens.get("refresh_expires_in") or 0),
            scopes=list(tokens.get("scopes") or []),
            display_name=str(display_name) if display_name else None,
            username=str(username) if username else None,
            avatar_url=str(avatar_url) if avatar_url else None,
        )
        self.learning.record_event(
            {
                "event_type": "oauth_connected",
                "draft_id": None,
                "payload": {"account_id": account.get("id"), "open_id": open_id},
            }
        )
        return {"ok": True, "account": account}

    def disconnect_account(self, account_id: str) -> dict[str, Any]:
        self._require_owner_module()
        revoke_ok = None
        raw = self.accounts.get_raw(account_id)
        if raw and raw.get("status") == "connected" and raw.get("access_token_sealed"):
            try:
                token = self.accounts.get_access_token(account_id)
                revoke_ok = bool(self.oauth.revoke(access_token=token).get("ok"))
            except ValueError:
                revoke_ok = False
        return self.accounts.disconnect(account_id, revoke_ok=revoke_ok)

    def sync_account(self, account_id: str) -> dict[str, Any]:
        self._require_owner_module()
        raw = self.accounts.get_raw(account_id)
        if not raw:
            raise ValueError("account_not_found")
        if raw.get("status") != "connected":
            raise ValueError("account_not_connected")
        # Refresh token if possible, then profile
        try:
            refresh = self.accounts.get_refresh_token(account_id)
        except ValueError:
            refresh = ""
        if refresh:
            refreshed = self.oauth.refresh_access_token(refresh_token=refresh)
            if refreshed.get("ok"):
                self.accounts.update_tokens(
                    account_id,
                    access_token=str(refreshed["access_token"]),
                    refresh_token=str(refreshed.get("refresh_token") or refresh),
                    expires_in=int(refreshed.get("expires_in") or 86400),
                    refresh_expires_in=int(refreshed.get("refresh_expires_in") or 0) or None,
                    scopes=list(refreshed.get("scopes") or []),
                )
        access = self.accounts.get_access_token(account_id)
        profile = self.oauth.fetch_user_profile(access_token=access)
        profile_fields = None
        if profile.get("ok"):
            profile_fields = {
                "display_name": profile.get("display_name"),
                "username": profile.get("username"),
                "avatar_url": profile.get("avatar_url"),
            }
        return self.accounts.mark_synced(account_id, profile=profile_fields)

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
