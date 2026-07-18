"""Video Factory v0 — CEO Horizon niche (TikTok first). Path A never imports this."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.feature_flags_service import load_features, try_build_scenario

_CHANNEL_ORDER = ("tiktok", "youtube_shorts", "instagram_reels")
_VALID_STAGES = frozenset({"dormant", "ready", "live"})

_DEFAULT_VIDEO_FACTORY: dict[str, Any] = {
    "channels": {
        "tiktok": {"stage": "dormant"},
        "youtube_shorts": {"stage": "dormant"},
        "instagram_reels": {"stage": "dormant"},
    },
    "capcut_connected": False,
    "payout_mode": "owner_platform_only",
}

REALITY_NOTE_RU = (
    "v0: текстовые сценарии и очередь статусов. Нет генерации MP4, нет автопубликации, "
    "нет CapCut. Вывод денег — только через кабинет TikTok владельца; Virtus Core не кошелёк."
)
REALITY_NOTE_DE = (
    "v0: Textszenarien und Status-Warteschlange. Kein MP4-Render, kein Auto-Publish, "
    "kein CapCut. Auszahlung nur über das TikTok-Konto des Owners — Virtus Core ist kein Wallet."
)

# Machine-readable — UI must gate on these, not on prose notes.
REALITY_FLAGS: dict[str, bool] = {
    "video_generation": False,
    "video_rendering": False,
    "trend_analysis": False,
    "tiktok_connector": False,
    "youtube_connector": False,
    "instagram_connector": False,
    "earn_money_inside_virtus": False,
}

_VALID_SOURCES = frozenset({"manual", "template", "imported", "ai_generated"})

# Registry of background worker names that Video Factory may start in future.
# v0: always empty — kill switch OFF must keep this empty.
_STARTED_VIDEO_WORKERS: list[str] = []


def reality_flags() -> dict[str, bool]:
    return dict(REALITY_FLAGS)


def capabilities_matrix(*, tiktok_enabled: bool) -> dict[str, Any]:
    """CEO Capability Matrix — what works today vs Horizon stubs."""
    return {
        "available": [
            {"id": "scenarios", "label_ru": "сценарии", "ok": True},
            {"id": "library", "label_ru": "библиотека", "ok": True},
            {"id": "queue", "label_ru": "очередь", "ok": True},
            {"id": "kill_switch", "label_ru": "kill switch", "ok": True},
        ],
        "unavailable": [
            {"id": "video_generation", "label_ru": "генерация видео", "ok": False},
            {"id": "publishing", "label_ru": "публикация", "ok": False},
            {"id": "tiktok_api", "label_ru": "TikTok API", "ok": False},
            {"id": "capcut", "label_ru": "CapCut", "ok": False},
            {"id": "earn_inside_virtus", "label_ru": "доход внутри Virtus", "ok": False},
        ],
        "tiktok_enabled": tiktok_enabled,
        "note_ru": "Доступные пункты работают при включённом kill switch; недоступные — Horizon.",
    }


def audit_video_factory_background(*, features: dict[str, Any] | None = None) -> dict[str, Any]:
    """Startup / test audit: when kill switch OFF, no Video Factory workers may run."""
    data = features if features is not None else load_features()
    enabled = data.get("tiktok_enabled") is True
    workers = list(_STARTED_VIDEO_WORKERS)
    # Reality flags must never claim live connectors in v0
    flags = reality_flags()
    illegal_true = [k for k, v in flags.items() if v is True]
    safe = (not workers) and (not illegal_true)
    if not enabled:
        # Extra: OFF must not have workers
        safe = safe and len(workers) == 0
    return {
        "name": "video_factory_workers",
        "ok": safe,
        "tiktok_enabled": enabled,
        "background_workers_started": workers,
        "publish_loops_started": False,
        "reality_flags": flags,
        "illegal_reality_true": illegal_true,
        "note_ru": (
            "Kill switch OFF → никаких background-процессов Video Factory. "
            "v0 не стартует воркеры даже при ON."
        ),
    }


def register_video_worker_for_tests(name: str) -> None:
    """Test-only hook to simulate a leaked worker."""
    _STARTED_VIDEO_WORKERS.append(name)


def clear_video_workers_for_tests() -> None:
    _STARTED_VIDEO_WORKERS.clear()


class VideoFactoryService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._root = memory_dir / "video_factory"
        self._root.mkdir(parents=True, exist_ok=True)
        self._library = self._root / "library.jsonl"
        self._drafts = self._root / "drafts.jsonl"
        self._queue = self._root / "queue.jsonl"

    def dashboard(self) -> dict[str, Any]:
        features = load_features()
        enabled = features.get("tiktok_enabled") is True
        vf = self._video_factory_cfg(features)
        drafts = self.list_drafts()
        library = self.list_library()
        queue = self.list_queue()
        return {
            "ok": True,
            "tiktok_enabled": enabled,
            "path_a_independent": True,
            "video_factory": vf,
            "counts": {
                "library": len(library),
                "drafts": len(drafts),
                "queue": len(queue),
                "approved": sum(1 for d in drafts if d.get("status") == "approved"),
            },
            "channels": self._channels_view(vf),
            "capcut": {
                "connected": bool(vf.get("capcut_connected")),
                "status_ru": "подключён" if vf.get("capcut_connected") else "не подключено",
                "status_de": "verbunden" if vf.get("capcut_connected") else "nicht verbunden",
            },
            "earnings": self.earnings_snapshot(),
            "trends": {
                "connected": False,
                "items": [],
                "note_ru": "Анализатор трендов не подключён — топ не имитируем.",
                "note_de": "Trend-Analysator nicht verbunden — keine Fake-Tops.",
            },
            "reality": reality_flags(),
            "reality_note_ru": REALITY_NOTE_RU,
            "reality_note_de": REALITY_NOTE_DE,
            "capabilities": capabilities_matrix(tiktok_enabled=enabled),
            "worker_audit": audit_video_factory_background(features=features),
        }

    def list_library(self) -> list[dict[str, Any]]:
        return self._read_jsonl(self._library)

    def add_library_item(self, meta: dict[str, Any]) -> dict[str, Any]:
        self._require_enabled()
        title = str(meta.get("title") or "").strip()[:200]
        if not title:
            raise ValueError("title_required")
        row = {
            "id": f"lib-{uuid.uuid4().hex[:10]}",
            "title": title,
            "niche": str(meta.get("niche") or "").strip()[:80] or None,
            "status": str(meta.get("status") or "stored")[:40],
            "source": str(meta.get("source") or "manual")[:40],
            "created_at": _now(),
            "note_ru": "Метаданные только — видеофайл в v0 не хранится.",
        }
        self._append_jsonl(self._library, row)
        return row

    def list_drafts(self) -> list[dict[str, Any]]:
        rows = self._read_jsonl(self._drafts)
        rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        return rows

    def create_draft_from_pattern(
        self,
        *,
        niche: str,
        city: str,
        pattern_issues: list[str],
        frequency_note: str = "",
        source: str = "manual",
    ) -> dict[str, Any]:
        self._require_enabled()
        src = (source or "manual").strip().lower()
        if src not in _VALID_SOURCES:
            raise ValueError("invalid_source")
        built = try_build_scenario(
            niche=niche,
            city=city,
            pattern_issues=list(pattern_issues or []),
            frequency_note=frequency_note or "",
        )
        if not built.get("ok"):
            raise ValueError(built.get("reason") or "scenario_failed")
        draft_body = built.get("draft") or {}
        row = {
            "id": f"draft-{uuid.uuid4().hex[:10]}",
            "status": "draft",
            "source": src,
            "created_at": _now(),
            "updated_at": _now(),
            "scenario": draft_body,
            "niche": draft_body.get("niche") or niche,
            "city": draft_body.get("city") or city,
        }
        self._append_jsonl(self._drafts, row)
        return row

    def approve_draft(self, draft_id: str) -> dict[str, Any]:
        self._require_enabled()
        row = self._update_draft(draft_id, status="approved")
        # Mirror into library as approved scenario card
        self._append_jsonl(
            self._library,
            {
                "id": f"lib-{uuid.uuid4().hex[:10]}",
                "title": (row.get("scenario") or {}).get("hook_de")
                or f"Draft {draft_id}",
                "niche": row.get("niche"),
                "status": "approved_scenario",
                "source": row.get("source") or "manual",
                "draft_id": draft_id,
                "created_at": _now(),
                "note_ru": "Утверждённый текстовый сценарий (без MP4).",
            },
        )
        return row

    def list_queue(self) -> list[dict[str, Any]]:
        rows = self._read_jsonl(self._queue)
        rows.sort(key=lambda r: r.get("queued_at") or "", reverse=True)
        return rows

    def queue_for_channel(self, draft_id: str, channel: str) -> dict[str, Any]:
        self._require_enabled()
        ch = (channel or "tiktok").strip().lower()
        if ch not in _CHANNEL_ORDER:
            raise ValueError("unsupported_channel")
        draft = self._get_draft(draft_id)
        if not draft:
            raise ValueError("draft_not_found")
        if draft.get("status") not in ("approved", "queued"):
            # auto-approve if still draft — CEO queued intentionally
            if draft.get("status") == "draft":
                draft = self._update_draft(draft_id, status="approved")
            else:
                raise ValueError("invalid_draft_status")
        self._update_draft(draft_id, status="queued")
        connector_ok = reality_flags().get(
            {"tiktok": "tiktok_connector", "youtube_shorts": "youtube_connector", "instagram_reels": "instagram_connector"}.get(
                ch, "tiktok_connector"
            ),
            False,
        )
        if connector_ok:
            # Future path — v0 never reaches here while REALITY_FLAGS stay false
            status = "queued"
            display_status = "Queued"
            block_code = None
            block_ru = None
            block_de = None
        else:
            status = "blocked"
            display_status = "Blocked"
            block_code = f"{ch}_connector_missing"
            block_ru = {
                "tiktok": "TikTok connector отсутствует",
                "youtube_shorts": "YouTube connector отсутствует",
                "instagram_reels": "Instagram connector отсутствует",
            }.get(ch, "Connector отсутствует")
            block_de = {
                "tiktok": "TikTok-Connector fehlt",
                "youtube_shorts": "YouTube-Connector fehlt",
                "instagram_reels": "Instagram-Connector fehlt",
            }.get(ch, "Connector fehlt")
        item = {
            "id": f"q-{uuid.uuid4().hex[:10]}",
            "draft_id": draft_id,
            "channel": ch,
            "status": status,
            "queue_state": "queued",
            "display_status": display_status,
            "block_reason_code": block_code,
            "block_reason_ru": block_ru,
            "block_reason_de": block_de,
            "publish_blocked": None if connector_ok else "awaiting_connector",
            "publish_note_ru": (
                None
                if connector_ok
                else f"Queued → Blocked. Причина: {block_ru}."
            ),
            "publish_note_de": (
                None
                if connector_ok
                else f"Queued → Blocked. Grund: {block_de}."
            ),
            "queued_at": _now(),
            "hook_de": (draft.get("scenario") or {}).get("hook_de"),
            "source": draft.get("source") or "manual",
        }
        self._append_jsonl(self._queue, item)
        return item

    def set_channel_stage(self, channel: str, stage: str) -> dict[str, Any]:
        """CEO advances channel launch sequence. Live still does not publish in v0."""
        self._require_enabled()
        ch = (channel or "").strip().lower()
        st = (stage or "").strip().lower()
        if ch not in _CHANNEL_ORDER:
            raise ValueError("unsupported_channel")
        if st not in _VALID_STAGES:
            raise ValueError("invalid_stage")
        # Sequential: youtube/instagram cannot go live before tiktok ready
        if ch != "tiktok" and st == "live":
            vf = self._video_factory_cfg(load_features())
            tiktok_stage = (vf.get("channels") or {}).get("tiktok", {}).get("stage")
            if tiktok_stage not in ("ready", "live"):
                raise ValueError("tiktok_first")
        from app.integration.feature_flags_service import update_video_factory_channel

        return update_video_factory_channel(channel=ch, stage=st)

    def earnings_snapshot(self) -> dict[str, Any]:
        return {
            "balance_in_virtus": 0,
            "currency": "EUR",
            "withdraw_via": "tiktok_owner_account",
            "payout_mode": "owner_platform_only",
            "note_ru": (
                "Прибыль и вывод — в кабинете TikTok владельца. "
                "Virtus Core считает статусы контента, не хранит и не выплачивает деньги."
            ),
            "note_de": (
                "Gewinn und Auszahlung nur im TikTok-Konto des Owners. "
                "Virtus Core trackt Content-Status — kein Wallet."
            ),
        }

    def _require_enabled(self) -> None:
        if load_features().get("tiktok_enabled") is not True:
            raise ValueError("tiktok_disabled")

    def _video_factory_cfg(self, features: dict[str, Any]) -> dict[str, Any]:
        raw = features.get("video_factory")
        if not isinstance(raw, dict):
            return json.loads(json.dumps(_DEFAULT_VIDEO_FACTORY))
        merged = json.loads(json.dumps(_DEFAULT_VIDEO_FACTORY))
        channels = raw.get("channels") if isinstance(raw.get("channels"), dict) else {}
        for key in _CHANNEL_ORDER:
            ch = channels.get(key) if isinstance(channels.get(key), dict) else {}
            stage = ch.get("stage") if ch.get("stage") in _VALID_STAGES else "dormant"
            merged["channels"][key] = {"stage": stage}
        merged["capcut_connected"] = bool(raw.get("capcut_connected"))
        merged["payout_mode"] = str(raw.get("payout_mode") or "owner_platform_only")
        return merged

    def _channels_view(self, vf: dict[str, Any]) -> list[dict[str, Any]]:
        labels = {
            "tiktok": "TikTok",
            "youtube_shorts": "YouTube Shorts",
            "instagram_reels": "Instagram Reels",
        }
        out: list[dict[str, Any]] = []
        for i, key in enumerate(_CHANNEL_ORDER):
            ch = (vf.get("channels") or {}).get(key) or {}
            out.append(
                {
                    "id": key,
                    "label": labels[key],
                    "stage": ch.get("stage") or "dormant",
                    "launch_order": i + 1,
                    "next_slot": i > 0,
                }
            )
        return out

    def _get_draft(self, draft_id: str) -> dict[str, Any] | None:
        for row in self._read_jsonl(self._drafts):
            if row.get("id") == draft_id:
                return row
        return None

    def _update_draft(self, draft_id: str, *, status: str) -> dict[str, Any]:
        rows = self._read_jsonl(self._drafts)
        found: dict[str, Any] | None = None
        for row in rows:
            if row.get("id") == draft_id:
                row["status"] = status
                row["updated_at"] = _now()
                found = row
                break
        if not found:
            raise ValueError("draft_not_found")
        self._write_jsonl(self._drafts, rows)
        return found

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            return []
        out: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                out.append(row)
        return out

    @staticmethod
    def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    @staticmethod
    def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
            encoding="utf-8",
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
