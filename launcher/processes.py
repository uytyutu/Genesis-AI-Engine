"""Start and stop Backend / Frontend child processes."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from launcher.branding import BRAND_NAME
from launcher.deps import backend_python_argv, find_python
from launcher.log_util import append_log
from launcher.paths import backend_dir, frontend_dir, log_dir
from launcher.runtime_state import clear_state, load_state, pid_alive, record_ops_running, sync_state


@dataclass
class ManagedProcesses:
    backend: subprocess.Popen | None = None
    frontend: subprocess.Popen | None = None


_reconnect_lock = threading.Lock()


def _no_window() -> int:
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return 0


def _kill_tree(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            capture_output=True,
            creationflags=_no_window(),
        )
    else:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def _frontend_exited(managed: ManagedProcesses | None) -> bool:
    if managed is None or managed.frontend is None:
        return False
    return managed.frontend.poll() is not None


def _backend_exited(managed: ManagedProcesses | None) -> bool:
    if managed is None or managed.backend is None:
        return False
    return managed.backend.poll() is not None


def _pid(proc: subprocess.Popen | None) -> int | None:
    if proc is None or proc.poll() is not None:
        return None
    return proc.pid


def sync_state_from_ports(
    managed: ManagedProcesses | None,
    root: Path | None = None,
) -> None:
    """Persist listener PIDs on :8000 / :3000 — ground truth for 24/7 attach."""
    from launcher.process_cleanup import backend_listener_pids, frontend_listener_pids

    be = _pid(managed.backend) if managed else None
    fe = _pid(managed.frontend) if managed else None
    be_ports = backend_listener_pids()
    fe_ports = frontend_listener_pids()
    if be_ports:
        be = be_ports[0]
    if fe_ports:
        fe = fe_ports[0]
    sync_state(be, fe, root=root)


def reconnect_managed(
    managed: ManagedProcesses,
    root: Path | None = None,
    *,
    restart_incompatible_backend: bool = False,
) -> bool:
    """Attach launcher UI to already-running Genesis processes.

    Returns True only when Mission Control is fully usable (backend + frontend HTTP 200)
    and the backend passes lifecycle checks (identity, age). Git is never consulted.

    When restart_incompatible_backend is False (idle status poll), a lifecycle problem is
    logged only — backend is not killed. Use True on explicit Start / launch paths.
    """
    with _reconnect_lock:
        return _reconnect_managed_locked(
            managed,
            root,
            restart_incompatible_backend=restart_incompatible_backend,
        )


def _reconnect_managed_locked(
    managed: ManagedProcesses,
    root: Path | None,
    *,
    restart_incompatible_backend: bool,
) -> bool:
    from launcher.backend_identity import (
        backend_runtime_compatible,
        fetch_backend_status,
        stop_backend_listeners,
    )
    from launcher.health import owner_ready_live, probe_backend_live, probe_frontend_live

    backend_up = probe_backend_live()
    frontend_up = probe_frontend_live()
    if not backend_up and not frontend_up:
        return False

    backend_compatible = True
    if backend_up:
        status = fetch_backend_status()
        compatible, reason = backend_runtime_compatible(root, status)
        if not compatible:
            backend_compatible = False
            append_log(f"Backend runtime mismatch — {reason}")
            if restart_incompatible_backend:
                append_log("Stopping incompatible backend before relaunch")
                result = stop_backend_listeners(root, managed)
                if not result.port_free:
                    detail = "; ".join(result.failures) or "port still occupied"
                    append_log(f"Backend stop incomplete: {detail}")
                backend_up = False
            else:
                append_log(
                    "Backend left running — press Start to relaunch if needed"
                )

    state = load_state(root)
    be_pid = state.get("backend_pid")
    fe_pid = state.get("frontend_pid")

    if backend_up and pid_alive(be_pid):
        managed.backend = _PopenStub(be_pid)  # type: ignore[assignment]
    from launcher.process_cleanup import backend_listener_pids, frontend_listener_pids

    be_ports = backend_listener_pids()
    if backend_up and be_ports:
        managed.backend = _PopenStub(be_ports[0])  # type: ignore[assignment]

    fe_ports = frontend_listener_pids()
    if frontend_up and fe_ports:
        managed.frontend = _PopenStub(fe_ports[0])  # type: ignore[assignment]
    elif frontend_up and pid_alive(fe_pid):
        managed.frontend = _PopenStub(fe_pid)  # type: ignore[assignment]

    if owner_ready_live() and backend_up and backend_compatible:
        return True

    if backend_up and not frontend_up:
        append_log("Partial 24/7: backend up, frontend down — will start frontend")
    return False


def services_running(root: Path | None = None) -> tuple[bool, bool]:
    from launcher.health import probe_backend_live, probe_frontend_live

    return probe_backend_live(), probe_frontend_live()


class _PopenStub:
    """Minimal stand-in when Genesis was started earlier and launcher reopened."""

    def __init__(self, pid: int) -> None:
        self.pid = pid

    def poll(self) -> int | None:
        return None if pid_alive(self.pid) else 1


def start_backend(root: Path | None = None) -> tuple[bool, str, subprocess.Popen | None]:
    from launcher.backend_identity import (
        backend_runtime_compatible,
        fetch_backend_status,
        stop_backend_listeners,
    )
    from launcher.backend_repair import prepare_backend_port
    from launcher.deps import ensure_backend_deps

    status = fetch_backend_status()
    if status is not None:
        compatible, reason = backend_runtime_compatible(root, status)
        if compatible:
            append_log(
                "Backend already serving /api/status — skip duplicate start"
            )
            return True, "Backend уже работает", None
        append_log(f"Incompatible backend on :8000 — {reason}; stopping before fresh start")
        result = stop_backend_listeners(root)
        if not result.port_free:
            detail = "; ".join(result.failures) or "port still occupied"
            return False, f"Не удалось остановить старый backend: {detail}", None

    python_argv = backend_python_argv()
    if not python_argv:
        from launcher.python_runtime import resolve_any_python, unsupported_python_message

        return False, unsupported_python_message(resolve_any_python()), None

    ok, msg = ensure_backend_deps(root)
    if not ok:
        return False, msg, None

    ok_port, port_msg = prepare_backend_port(root)
    if not ok_port:
        return False, port_msg, None

    log_file = log_dir(root) / "backend.log"
    log_handle = open(log_file, "a", encoding="utf-8")
    be = backend_dir(root)

    proc = subprocess.Popen(
        [*python_argv, "-m", "uvicorn", "app.main:app", "--port", "8000"],
        cwd=be,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        creationflags=_no_window(),
    )
    append_log(f"Backend started pid={proc.pid}")
    return True, f"Backend запущен (журнал: {log_file})", proc


def _start_frontend_dev(
    root: Path | None,
    *,
    managed: ManagedProcesses | None = None,
    on_phase: Callable[[str], None] | None = None,
    on_progress: Callable[[str], None] | None = None,
) -> tuple[bool, str, subprocess.Popen | None]:
    """CEO daily path — next dev when production build is missing or corrupt."""
    from launcher.deps import augmented_path, ensure_frontend_ready, find_npm
    from launcher.health import probe_frontend_live
    from launcher.process_cleanup import frontend_listener_pids, stop_frontend_listeners

    if probe_frontend_live(idle=True):
        append_log("Frontend dev already serving :3000")
        sync_state_from_ports(managed, root)
        return True, "Mission Control уже работает (dev)", None

    if on_phase:
        on_phase("frontend")
    if on_progress:
        on_progress("Zapuskayu Mission Control (dev)...")

    stop_frontend_listeners(root, managed)
    time.sleep(0.5)

    ok, msg = ensure_frontend_ready(root, for_production=False, managed=managed)
    if not ok:
        return False, msg, None

    npm = find_npm()
    if not npm:
        return False, "Node.js / npm не найдены.", None

    fe = frontend_dir(root)
    log_file = log_dir(root) / "frontend.log"
    log_handle = open(log_file, "a", encoding="utf-8")
    env = os.environ.copy()
    env["PATH"] = augmented_path()
    env["PORT"] = "3000"
    proc = subprocess.Popen(
        [npm, "run", "dev"],
        cwd=fe,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        shell=False,
        env=env,
        creationflags=_no_window(),
    )
    append_log(f"Frontend started npm_pid={proc.pid} mode=dev (next dev)")
    deadline = time.time() + 180.0
    while time.time() < deadline:
        if probe_frontend_live(idle=True):
            sync_state_from_ports(managed, root)
            fe_ports = frontend_listener_pids()
            listener = fe_ports[0] if fe_ports else proc.pid
            append_log(f"Frontend dev ready pid={listener} HTTP 200 on :3000")
            return True, f"Mission Control готов (dev · {log_file})", proc
        if proc.poll() is not None:
            return False, "Frontend dev завершился — см. frontend.log", None
        time.sleep(1.0)

    sync_state_from_ports(managed, root)
    return True, f"Mission Control запускается (dev · {log_file})", proc


def start_frontend(
    root: Path | None = None,
    *,
    managed: ManagedProcesses | None = None,
    build_policy: str = "launch_stable",
    on_phase: Callable[[str], None] | None = None,
    on_progress: Callable[[str], None] | None = None,
) -> tuple[bool, str, subprocess.Popen | None]:
    from launcher.deps import (
        augmented_path,
        clear_frontend_build,
        ensure_frontend_ready,
        find_npm,
        frontend_build_integrity,
    )
    from launcher.frontend_build_policy import POLICY_DEV_SERVER, POLICY_REBUILD_NOW
    from launcher.health import frontend_port_listening, probe_frontend_live
    from launcher.process_cleanup import frontend_listener_pids, stop_frontend_listeners

    if build_policy == POLICY_DEV_SERVER or not frontend_build_integrity(root):
        append_log("CEO path: production unavailable — using next dev")
        return _start_frontend_dev(
            root,
            managed=managed,
            on_phase=on_phase,
            on_progress=on_progress,
        )

    if probe_frontend_live(idle=True):
        append_log("Frontend already serving :3000 — skip duplicate start")
        sync_state_from_ports(managed, root)
        return True, "Virtus Core уже работает на :3000", None

    fe = frontend_dir(root)

    # Process alive but not HTTP 200 — stop before rebuild/start.
    if frontend_port_listening() and not probe_frontend_live(idle=True):
        append_log("Frontend listener on :3000 without HTTP 200 — stopping before restart")
        stop_frontend_listeners(root, managed)
        time.sleep(0.5)

    if (fe / ".next").exists() and not frontend_build_integrity(root):
        append_log("Incomplete .next — stop Frontend, clear, rebuild")
        clear_frontend_build(root, managed=managed)

    def _build_progress(label: str) -> None:
        if on_phase:
            on_phase("build_frontend")
        if on_progress:
            on_progress(label)

    ok, msg = ensure_frontend_ready(
        root,
        for_production=True,
        managed=managed,
        build_policy=build_policy,
        on_build_progress=_build_progress,
    )
    if not ok:
        return False, msg, None

    npm = find_npm()
    if not npm:
        return False, "Node.js / npm не найдены. Запустите Virtus Core — установка в один клик.", None

    log_file = log_dir(root) / "frontend.log"
    log_handle = open(log_file, "a", encoding="utf-8")

    env = os.environ.copy()
    env["PATH"] = augmented_path()
    env["PORT"] = "3000"
    proc = subprocess.Popen(
        [npm, "run", "start"],
        cwd=fe,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        shell=False,
        env=env,
        creationflags=_no_window(),
    )
    from launcher.process_cleanup import frontend_listener_pids
    from launcher.health import probe_frontend_live

    append_log(f"Frontend started npm_pid={proc.pid} mode=production (next start)")
    deadline = time.time() + 30.0
    while time.time() < deadline:
        if probe_frontend_live():
            sync_state_from_ports(managed, root)
            fe_ports = frontend_listener_pids()
            listener = fe_ports[0] if fe_ports else proc.pid
            append_log(f"Frontend listener pid={listener} HTTP 200 on :3000")
            return True, f"Virtus Core запущен — production (журнал: {log_file})", proc
        if proc.poll() is not None:
            return False, "Frontend завершился сразу после запуска — см. frontend.log", None
        time.sleep(0.5)

    sync_state_from_ports(managed, root)
    return True, f"Virtus Core запущен — ожидание HTTP 200 (журнал: {log_file})", proc


def _kill_pid(pid: int | None) -> None:
    if not pid or not pid_alive(pid):
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            creationflags=_no_window(),
        )
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass


def stop_all(managed: ManagedProcesses, root: Path | None = None) -> None:
    from launcher.process_cleanup import kill_genesis_ports

    state = load_state(root)
    _kill_tree(managed.frontend)
    _kill_tree(managed.backend)
    if managed.frontend is None:
        _kill_pid(state.get("frontend_pid"))
    if managed.backend is None:
        _kill_pid(state.get("backend_pid"))
    kill_genesis_ports(root)
    managed.frontend = None
    managed.backend = None
    clear_state(root)
    append_log(f"{BRAND_NAME} остановлен")


def launch_genesis(
    managed: ManagedProcesses,
    root: Path | None = None,
    install_deps: bool = True,
    on_phase: Callable[[str], None] | None = None,
    on_progress: Callable[[str], None] | None = None,
    build_policy: str = "launch_stable",
) -> tuple[bool, str]:
    from launcher.backend_identity import (
        backend_runtime_compatible,
        fetch_backend_status,
        stop_backend_listeners,
    )
    from launcher.deps import check_dependencies, install_backend_deps
    from launcher.health import owner_ready_live, probe_backend_live, probe_frontend_live

    if owner_ready_live(idle=True):
        status = fetch_backend_status()
        compatible, reason = backend_runtime_compatible(root, status)
        if compatible:
            reconnect_managed(managed, root)
            sync_state_from_ports(managed, root)
            record_ops_running(root)
            return True, "Virtus Core уже работает — подключено (24/7)"
        append_log(f"Incompatible backend {BRAND_NAME} on Start — {reason}")
        result = stop_backend_listeners(root, managed)
        if not result.port_free:
            detail = "; ".join(result.failures) or "port still occupied"
            return False, f"Не удалось остановить старый backend: {detail}", None

    deps = check_dependencies(root)
    messages: list[str] = []

    if not deps.python_ok:
        return False, "Установите Python 3.11+ с python.org"

    if install_deps:
        ok, msg = install_backend_deps(root, force=False)
        messages.append(msg)
        if not ok:
            return False, msg

    if on_phase:
        on_phase("backend")

    backend_up, frontend_up = services_running(root)
    if backend_up and (managed.backend is None or managed.backend.poll() is not None):
        reconnect_managed(managed, root)
        messages.append("Backend уже работает — подключено (24/7)")
    elif managed.backend is None or managed.backend.poll() is not None:
        if not backend_up:
            from launcher.backend_repair import prepare_backend_port

            ok_port, port_msg = prepare_backend_port(root)
            messages.append(port_msg)
            if not ok_port:
                return False, port_msg
        ok, msg, proc = start_backend(root)
        messages.append(msg)
        if not ok:
            return False, msg
        if proc is not None:
            managed.backend = proc
        elif probe_backend_live():
            reconnect_managed(managed, root)
            messages.append("Backend подключён — уже работал на :8000")

    if deps.node_ok:
        from launcher.health import probe_backend_live

        if on_phase:
            on_phase("install_frontend")
        from launcher.deps import ensure_frontend_ready
        from launcher.health import probe_frontend_live

        # Wait for backend after we started it — do not abort the whole launch on a slow boot.
        backend_wait_deadline = time.time() + 45.0
        while time.time() < backend_wait_deadline and not probe_backend_live():
            time.sleep(0.5)

        ok, msg = ensure_frontend_ready(root, for_production=False)
        messages.append(msg)
        if not ok:
            return False, msg
        if on_phase:
            on_phase("frontend")
        frontend_live = probe_frontend_live(idle=True)
        if frontend_live and (managed.frontend is None or managed.frontend.poll() is not None):
            reconnect_managed(managed, root)
            messages.append("Frontend уже работает — подключено (24/7)")
        elif not frontend_live and (managed.frontend is None or managed.frontend.poll() is not None):
            ok, msg, proc = start_frontend(
                root,
                managed=managed,
                build_policy=build_policy,
                on_phase=on_phase,
                on_progress=on_progress,
            )
            messages.append(msg)
            if not ok:
                return False, msg
            if proc is not None:
                managed.frontend = proc
            elif probe_frontend_live():
                reconnect_managed(managed, root)
                messages.append("Frontend подключён — уже работал на :3000")
    else:
        messages.append("Node.js — нажмите «Запустить» для установки Mission Control")
        return False, (
            "Node.js не найден — Mission Control не может запуститься.\n"
            "Нажмите «Запустить» — Virtus Core установит Node.js автоматически."
        )

    sync_state_from_ports(managed, root)
    record_ops_running(root)
    return True, "\n".join(messages)


def _record_recovery(message: str, root: Path | None) -> None:
    from launcher.dogfooding import record_auto_recovery

    record_auto_recovery(message, root=root)


def wait_until_ready(
    timeout: float = 120.0,
    poll: float = 0.8,
    *,
    managed: ManagedProcesses | None = None,
    root: Path | None = None,
    on_progress: Callable[[str], None] | None = None,
    auto_repair: bool = True,
) -> tuple[bool, str]:
    from launcher.backend_repair import (
        backend_log_indicates_error,
        repair_backend,
    )
    from launcher.deps import check_dependencies
    from launcher.frontend_repair import (
        frontend_log_indicates_error,
        repair_frontend,
    )
    from launcher.health import (
        frontend_port_listening,
        owner_ready_live,
        probe_backend_live,
        probe_frontend_live,
        probe_vector_chat_ready,
        startup_progress_message,
    )
    from launcher.startup_stages import assess_startup, failure_for_stage

    MAX_TOTAL_SEC = 150.0
    REPAIR_BACKEND_SEC = 20.0
    REPAIR_FRONTEND_SEC = 20.0
    ALIVE_NOT_READY_SEC = 2.0

    def _sync() -> None:
        sync_state_from_ports(managed, root)

    if owner_ready_live():
        _sync()
        return True, ""

    started = time.time()
    deadline = min(started + timeout, started + MAX_TOTAL_SEC)
    backend_repair_attempted = False
    frontend_repair_attempted = False
    last_progress_sec = -1
    alive_not_ready_since: float | None = None

    while time.time() < deadline:
        elapsed = time.time() - started
        sec = int(elapsed)

        if owner_ready_live():
            _sync()
            return True, ""

        assessment = assess_startup(root)

        if on_progress and sec > 0 and sec != last_progress_sec and sec % 2 == 0:
            last_progress_sec = sec
            on_progress(
                startup_progress_message(
                    backend_up=probe_backend_live(),
                    frontend_up=probe_frontend_live(),
                    vector_ready=probe_vector_chat_ready(),
                    elapsed_sec=sec,
                )
            )

        # --- Stage 1: Backend only ---
        if not probe_backend_live():
            if _backend_exited(managed) or (
                backend_log_indicates_error(root) and not probe_backend_live()
            ):
                if auto_repair and not backend_repair_attempted and managed is not None:
                    if owner_ready_live():
                        _sync()
                        return True, ""
                    backend_repair_attempted = True
                    if on_progress:
                        on_progress("🟡 Исправление Backend...")
                    ok, repair_msg = repair_backend(managed, root)
                    append_log(f"Staged repair backend: {repair_msg}")
                    if ok and probe_backend_live():
                        _record_recovery(repair_msg, root)
                        deadline = min(time.time() + 40.0, started + MAX_TOTAL_SEC)
                        continue
                return False, failure_for_stage(root, elapsed_sec=elapsed)

            if auto_repair and not backend_repair_attempted and managed is not None and elapsed >= REPAIR_BACKEND_SEC:
                backend_repair_attempted = True
                if on_progress:
                    on_progress("🟡 Исправление Backend...")
                ok, repair_msg = repair_backend(managed, root)
                append_log(f"Staged repair backend (timeout): {repair_msg}")
                if ok and probe_backend_live():
                    _record_recovery(repair_msg, root)
                    deadline = min(time.time() + 40.0, started + MAX_TOTAL_SEC)
                    continue
                return False, failure_for_stage(root, elapsed_sec=elapsed)

            time.sleep(poll)
            continue

        # --- Stage 2+: Frontend only after Backend responds ---
        if probe_frontend_live():
            _sync()
            return True, ""

        if (
            probe_backend_live()
            and frontend_port_listening()
            and not probe_frontend_live()
        ):
            if alive_not_ready_since is None:
                alive_not_ready_since = time.time()
            elif (
                time.time() - alive_not_ready_since >= ALIVE_NOT_READY_SEC
                and not frontend_repair_attempted
                and managed is not None
            ):
                frontend_repair_attempted = True
                alive_not_ready_since = None
                if on_progress:
                    on_progress("🟡 Frontend жив, но не HTTP 200 — перезапуск...")
                append_log("Frontend alive on :3000 without HTTP 200 — restart with safe rebuild")
                ok, repair_msg = repair_frontend(managed, root)
                append_log(f"Product restart frontend: {repair_msg}")
                if ok and probe_frontend_live():
                    _record_recovery(repair_msg, root)
                    _sync()
                    return True, ""
                deadline = min(time.time() + 60.0, started + MAX_TOTAL_SEC)
                continue
        else:
            alive_not_ready_since = None

        if _frontend_exited(managed):
            if probe_frontend_live():
                reconnect_managed(managed, root)
                _sync()
                return True, ""
            if auto_repair and not frontend_repair_attempted and managed is not None:
                frontend_repair_attempted = True
                if on_progress:
                    on_progress("🟡 Исправление Frontend...")
                ok, repair_msg = repair_frontend(managed, root)
                append_log(f"Staged repair frontend (crashed): {repair_msg}")
                if ok and probe_frontend_live():
                    _record_recovery(repair_msg, root)
                    _sync()
                    return True, ""
            return False, failure_for_stage(root, frontend_exited=True, elapsed_sec=elapsed)

        if frontend_log_indicates_error(root) and not probe_frontend_live():
            if auto_repair and not frontend_repair_attempted and managed is not None:
                if owner_ready_live():
                    _sync()
                    return True, ""
                frontend_repair_attempted = True
                if on_progress:
                    on_progress("🟡 Исправление Frontend...")
                ok, repair_msg = repair_frontend(managed, root)
                append_log(f"Staged repair frontend (log): {repair_msg}")
                if ok and probe_frontend_live():
                    _record_recovery(repair_msg, root)
                    _sync()
                    return True, ""
            return False, failure_for_stage(root, elapsed_sec=elapsed)

        if (
            auto_repair
            and not frontend_repair_attempted
            and managed is not None
            and elapsed >= REPAIR_FRONTEND_SEC
            and probe_backend_live()
            and not probe_frontend_live()
        ):
            frontend_repair_attempted = True
            if on_progress:
                on_progress("🟡 Исправление Frontend...")
            ok, repair_msg = repair_frontend(managed, root)
            append_log(f"Staged repair frontend (timeout): {repair_msg}")
            if ok and probe_frontend_live():
                _record_recovery(repair_msg, root)
                _sync()
                return True, ""
            return False, failure_for_stage(root, elapsed_sec=elapsed)

        deps = check_dependencies(root)
        if not deps.node_ok:
            return False, failure_for_stage(root, elapsed_sec=elapsed)

        time.sleep(poll)

    if owner_ready_live():
        _sync()
        return True, ""

    return False, failure_for_stage(root, elapsed_sec=time.time() - started)


def _probe_url_quick() -> bool:
    from launcher.health import probe_frontend_live

    return probe_frontend_live()
