#!/usr/bin/env python3
"""CEO Final Verification — 10x real Genesis.exe GUI cycles (not programmatic).

Simulates Desktop path:
  Genesis.exe → Launcher window → ▶ Запустить Genesis → HTTP 200 → close → repeat

Run from repo root:
    py scripts/ceo_gui_verification.py --cycles 10
"""

from __future__ import annotations

import argparse
import ctypes
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if sys.platform != "win32":
    raise SystemExit("CEO GUI verification requires Windows.")

from ctypes import wintypes

user32 = ctypes.windll.user32


def _prepare_launcher_config(root: Path) -> None:
    from launcher.config import LauncherConfig
    from launcher.paths import memory_dir

    memory_dir(root).mkdir(parents=True, exist_ok=True)
    cfg = LauncherConfig.load()
    cfg.first_run_complete = True
    cfg.auto_start_on_open = False
    cfg.auto_open_browser = True
    cfg.keep_running_on_close = False
    if not cfg.project_root:
        cfg.project_root = str(root.resolve())
    cfg.save()


def _genesis_exe(root: Path) -> Path:
    exe = root / "dist" / "Genesis.exe"
    if not exe.is_file():
        raise FileNotFoundError(
            f"Genesis.exe not found: {exe}\nRun: .\\launcher\\build.ps1"
        )
    return exe.resolve()


def _find_genesis_hwnd(timeout: float = 45.0) -> int | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        found: list[int] = []

        def callback(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.strip()
            if title == "Genesis" or title.startswith("Genesis "):
                found.append(hwnd)
            return True

        cb = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(callback)
        user32.EnumWindows(cb, 0)
        if found:
            return found[0]
        time.sleep(0.3)
    return None


def _window_rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom


def _click(hwnd: int, x: int, y: int) -> None:
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.2)
    user32.SetCursorPos(x, y)
    time.sleep(0.05)
    user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
    user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP


def _click_start_button(hwnd: int) -> None:
    """Click ▶ Запустить Genesis — primary control below status label."""
    left, top, right, bottom = _window_rect(hwnd)
    cx = (left + right) // 2
    # Empirical offset for 460x780 window layout (status + start button).
    cy = top + 195
    _click(hwnd, cx, cy)


def _close_launcher(hwnd: int, exe_pid: int) -> None:
    user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
    time.sleep(1.5)
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(exe_pid)],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass


def _wait_ready(timeout: float) -> tuple[bool, str]:
    from launcher.health import owner_ready_live, probe_frontend_http_status

    deadline = time.time() + timeout
    while time.time() < deadline:
        if owner_ready_live():
            return True, "HTTP 200"
        status = probe_frontend_http_status()
        if status is not None and status != 200:
            return False, f"Frontend HTTP {status} (expected 200)"
        time.sleep(0.8)
    return False, "timeout waiting for HTTP 200"


def run_gui_cycle(cycle: int, root: Path, exe: Path, *, timeout: float) -> tuple[bool, str]:
    from launcher.processes import ManagedProcesses, stop_all

    stop_all(ManagedProcesses(), root)
    time.sleep(1)

    proc = subprocess.Popen([str(exe)], cwd=str(exe.parent))
    try:
        hwnd = _find_genesis_hwnd(timeout=45.0)
        if not hwnd:
            return False, f"cycle {cycle}: Launcher window not found"

        time.sleep(1.5)
        _click_start_button(hwnd)

        ok, detail = _wait_ready(timeout)
        if not ok:
            return False, f"cycle {cycle}: {detail}"

        stop_all(ManagedProcesses(), root)
        _close_launcher(hwnd, proc.pid)
        time.sleep(1)
        return True, f"cycle {cycle} OK (Genesis.exe GUI path)"
    finally:
        if proc.poll() is None:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        stop_all(ManagedProcesses(), root)


def main() -> int:
    parser = argparse.ArgumentParser(description="CEO Final Verification — Genesis.exe GUI cycles")
    parser.add_argument("--cycles", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    from launcher.paths import find_project_root
    from launcher.release_guardian import (
        PRODUCT_NOT_READY,
        READY_FOR_CEO_VERIFY,
        evaluate_launch_pipeline,
    )
    from launcher.launch_pipeline_state import record_gui_cycles

    root = find_project_root(ROOT)
    _prepare_launcher_config(root)
    exe = _genesis_exe(root)

    print(f"CEO GUI verification x{args.cycles}")
    print(f"Executable: {exe}")
    print("=" * 40)

    failures: list[str] = []
    for i in range(1, args.cycles + 1):
        print(f"GUI cycle {i}/{args.cycles}...", flush=True)
        ok, detail = run_gui_cycle(i, root, exe, timeout=args.timeout)
        print(f"  {'OK' if ok else 'FAIL'}  {detail}")
        if not ok:
            failures.append(detail)

    print("=" * 40)
    if failures:
        print(f"FAILED {len(failures)}/{args.cycles}")
        for f in failures:
            print(f"  - {f}")
        print(PRODUCT_NOT_READY)
        return 1

    record_gui_cycles(args.cycles, root)
    verdict = evaluate_launch_pipeline(min_cycles=args.cycles)
    print(f"PASSED all {args.cycles} GUI cycles")
    try:
        print(verdict.render())
    except UnicodeEncodeError:
        print(verdict.render().encode("ascii", errors="replace").decode("ascii"))
    if verdict.headline == "READY FOR CEO VERIFY":
        print(READY_FOR_CEO_VERIFY)
    return 0 if verdict.headline in ("READY FOR CEO VERIFY", "ДА") else 1


if __name__ == "__main__":
    raise SystemExit(main())
