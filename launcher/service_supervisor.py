"""Background service supervisor — soft-restart Frontend without full Genesis reboot.

RC1-D: Kill FE → detect DOWN → restart FE only → Backend stays up.
Must keep running while Virtus Core is alive (including when the control panel is hidden).
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from launcher.log_util import append_log

if TYPE_CHECKING:
    from launcher.processes import ManagedProcesses

_POLL_SEC = 12.0
_REPAIR_COOLDOWN_SEC = 45.0
_FE_DOWN_CONFIRM_SEC = 8.0


class ServiceSupervisor:
    """Watch Backend/Frontend ports and soft-restart Frontend only when needed."""

    def __init__(
        self,
        managed: ManagedProcesses,
        root: Path | None = None,
        *,
        poll_sec: float = _POLL_SEC,
        repair_cooldown_sec: float = _REPAIR_COOLDOWN_SEC,
    ) -> None:
        self._managed = managed
        self._root = root
        self._poll_sec = poll_sec
        self._repair_cooldown_sec = repair_cooldown_sec
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_fe_repair_at = 0.0
        self._fe_down_since: float | None = None
        self._lock = threading.Lock()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        with self._lock:
            if self.running:
                return
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._loop,
                name="virtus-service-supervisor",
                daemon=True,
            )
            self._thread.start()
            append_log("Supervisor: started (FE soft-restart watchdog)")

    def stop(self) -> None:
        with self._lock:
            self._stop.set()
            thread = self._thread
            self._thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        append_log("Supervisor: stopped")

    def note_frontend_repaired(self) -> None:
        self._last_fe_repair_at = time.monotonic()
        self._fe_down_since = None

    def _loop(self) -> None:
        while not self._stop.wait(self._poll_sec):
            try:
                self._tick()
            except Exception as exc:
                append_log(f"Supervisor tick error: {exc}")

    def _tick(self) -> None:
        from launcher.health import probe_backend_live, probe_frontend_live

        backend_up = probe_backend_live(idle=True)
        frontend_up = probe_frontend_live(idle=True)
        now = time.monotonic()

        if not backend_up:
            self._fe_down_since = None
            return

        if frontend_up:
            self._fe_down_since = None
            return

        if self._fe_down_since is None:
            self._fe_down_since = now
            append_log("Supervisor: Frontend DOWN detected (confirming…)")
            return

        if now - self._fe_down_since < _FE_DOWN_CONFIRM_SEC:
            return

        if now - self._last_fe_repair_at < self._repair_cooldown_sec:
            return

        self._last_fe_repair_at = now
        append_log(
            "Supervisor recovery: Frontend DOWN — soft restart only (backend untouched)"
        )
        from launcher.frontend_repair import repair_frontend
        from launcher.processes import sync_state_from_ports

        try:
            ok, msg = repair_frontend(
                self._managed, self._root, allow_rebuild=False
            )
            append_log(f"Supervisor Frontend recovery: ok={ok} {msg}")
            if ok:
                sync_state_from_ports(self._managed, self._root)
                self._fe_down_since = None
        except Exception as exc:
            append_log(f"Supervisor Frontend recovery failed: {exc}")
