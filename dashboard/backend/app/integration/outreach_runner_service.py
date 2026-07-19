"""Country Desk runner — Start/Stop with visible ticks (hunt → draft → optional send).

Does not bypass CEO Approve unless outreach is enabled and a lead is already
approved / high-win auto-confirm path. Exclusion still blocks re-contact.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OutreachRunnerService:
    def __init__(
        self,
        memory_dir: Path | None,
        *,
        refresh_fn: Callable[..., dict[str, Any]] | None = None,
        send_next_fn: Callable[[], dict[str, Any]] | None = None,
        interval_fn: Callable[[], int] | None = None,
    ) -> None:
        self._memory = memory_dir
        self._refresh_fn = refresh_fn
        self._send_next_fn = send_next_fn
        self._interval_fn = interval_fn

    def _path(self) -> Path | None:
        if not self._memory:
            return None
        return Path(self._memory) / "outreach_runner_state.json"

    def _load(self) -> dict[str, Any]:
        empty = {
            "running": False,
            "started_at": None,
            "stopped_at": None,
            "ticks": 0,
            "session_leads": 0,
            "session_drafts": 0,
            "session_sends": 0,
            "session_skipped": 0,
            "last_action": None,
            "last_message_ru": None,
            "last_tick_at": None,
            "next_tick_at": None,
            "log": [],
        }
        path = self._path()
        if not path or not path.is_file():
            return empty
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return empty
        if not isinstance(data, dict):
            return empty
        for k, v in empty.items():
            data.setdefault(k, v)
        return data

    def _save(self, data: dict[str, Any]) -> None:
        path = self._path()
        if not path:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _interval(self) -> int:
        if self._interval_fn:
            try:
                return max(15, int(self._interval_fn()))
            except Exception:
                pass
        return 90

    def _log(self, state: dict[str, Any], action: str, message_ru: str) -> None:
        entry = {
            "at": _utc_now().isoformat(),
            "action": action,
            "message_ru": message_ru,
        }
        log = list(state.get("log") or [])
        log.append(entry)
        state["log"] = log[-40:]
        state["last_action"] = action
        state["last_message_ru"] = message_ru

    def start(self) -> dict[str, Any]:
        state = self._load()
        if state.get("running"):
            return self.status()
        now = _utc_now()
        interval = self._interval()
        state.update(
            {
                "running": True,
                "started_at": now.isoformat(),
                "stopped_at": None,
                "ticks": 0,
                "session_leads": 0,
                "session_drafts": 0,
                "session_sends": 0,
                "session_skipped": 0,
                "last_tick_at": None,
                "next_tick_at": now.isoformat(),
            }
        )
        self._log(
            state,
            "start",
            f"Пуск Country Desk · все страны round-robin · тик ~{interval}с · письмо только Approve/квота",
        )
        self._save(state)
        return self.status()

    def stop(self) -> dict[str, Any]:
        state = self._load()
        state["running"] = False
        state["stopped_at"] = _utc_now().isoformat()
        state["next_tick_at"] = None
        self._log(state, "stop", "Стоп · генерация и тики остановлены")
        self._save(state)
        return self.status()

    def status(self) -> dict[str, Any]:
        state = self._load()
        outreach_on = os.getenv("GENESIS_OUTREACH_ENABLED", "").strip().lower() == "true"
        return {
            "ok": True,
            "running": bool(state.get("running")),
            "started_at": state.get("started_at"),
            "stopped_at": state.get("stopped_at"),
            "ticks": int(state.get("ticks") or 0),
            "session_leads": int(state.get("session_leads") or 0),
            "session_drafts": int(state.get("session_drafts") or 0),
            "session_sends": int(state.get("session_sends") or 0),
            "session_skipped": int(state.get("session_skipped") or 0),
            "last_action": state.get("last_action"),
            "last_message_ru": state.get("last_message_ru"),
            "last_tick_at": state.get("last_tick_at"),
            "next_tick_at": state.get("next_tick_at"),
            "interval_sec": self._interval(),
            "outreach_send_enabled": outreach_on,
            "log": list(state.get("log") or [])[-15:],
            "note_ru": (
                "Пуск = hunt/draft round-robin по всем enabled странам до их лимитов. "
                "Паузы adaptive пропускаются. Повторные компании — exclusion. "
                "Автоотправка только при GENESIS_OUTREACH_ENABLED + Approve/high-win."
            ),
        }

    def tick(self) -> dict[str, Any]:
        state = self._load()
        if not state.get("running"):
            return {**self.status(), "ticked": False, "reason": "stopped"}

        now = _utc_now()
        interval = self._interval()
        actions: list[str] = []
        detail: dict[str, Any] = {}

        # Prefer one send attempt if enabled (approved queue) — still respects quota/exclusion.
        send_enabled = os.getenv("GENESIS_OUTREACH_ENABLED", "").strip().lower() == "true"
        if send_enabled and self._send_next_fn:
            try:
                send_res = self._send_next_fn()
                detail["send"] = send_res
                if send_res.get("sent"):
                    state["session_sends"] = int(state.get("session_sends") or 0) + 1
                    actions.append("send")
                    self._log(
                        state,
                        "send",
                        f"Отправлено: {send_res.get('company') or send_res.get('to') or 'ok'}",
                    )
                elif send_res.get("skipped"):
                    state["session_skipped"] = int(state.get("session_skipped") or 0) + 1
                    actions.append("send_skip")
                    self._log(
                        state,
                        "send_skip",
                        str(send_res.get("message_ru") or send_res.get("reason") or "пропуск отправки"),
                    )
            except Exception as exc:
                actions.append("send_error")
                self._log(state, "send_error", f"Ошибка отправки: {exc}")

        # Always try to refresh/draft a small batch so the queue fills.
        if self._refresh_fn:
            try:
                refresh = self._refresh_fn(limit=3, auto_confirm=True)
                detail["refresh"] = {
                    "ok": refresh.get("ok"),
                    "message_ru": refresh.get("message_ru"),
                }
                drafts = refresh.get("drafts") or {}
                created = int(drafts.get("created") or 0)
                drafted = int(drafts.get("drafted") or 0)
                state["session_leads"] = int(state.get("session_leads") or 0) + created
                state["session_drafts"] = int(state.get("session_drafts") or 0) + drafted
                actions.append("hunt_draft")
                self._log(
                    state,
                    "hunt_draft",
                    refresh.get("message_ru")
                    or f"Hunt/draft: created={created} drafted={drafted}",
                )
            except Exception as exc:
                actions.append("hunt_error")
                self._log(state, "hunt_error", f"Ошибка hunt: {exc}")

        state["ticks"] = int(state.get("ticks") or 0) + 1
        state["last_tick_at"] = now.isoformat()
        from datetime import timedelta

        state["next_tick_at"] = (now + timedelta(seconds=interval)).isoformat()
        self._save(state)
        return {
            **self.status(),
            "ticked": True,
            "actions": actions,
            "detail": detail,
        }
