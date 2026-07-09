"""Collect Launcher hang/freeze diagnostics into diagnostics/<timestamp>/."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from launcher import build_info, paths
from launcher.log_util import append_log


def _no_window() -> int:
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return 0


def _tail_text(path: Path, lines: int = 30) -> str:
    if not path.is_file():
        return f"(файл не найден: {path})\n"
    try:
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return f"(ошибка чтения {path}: {exc})\n"
    if len(content) <= lines:
        return "\n".join(content) + ("\n" if content else "")
    return "\n".join(content[-lines:]) + "\n"


def _find_genesis_pids() -> list[int]:
    if sys.platform != "win32":
        return []
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Process -Name Genesis -ErrorAction SilentlyContinue | "
                "Select-Object -ExpandProperty Id",
            ],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=_no_window(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    pids: list[int] = []
    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if line.isdigit():
            pids.append(int(line))
    return pids


def _process_report() -> str:
    if sys.platform != "win32":
        return "process list: Windows only\n"
    script = """
$names = 'Genesis','python','py','node','nodejs'
Get-Process -ErrorAction SilentlyContinue | Where-Object { $names -contains $_.ProcessName } |
  Select-Object Id, ProcessName, Responding, CPU, StartTime, Path |
  Format-Table -AutoSize | Out-String -Width 200
"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=_no_window(),
        )
        return (result.stdout or "") + (result.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"process report failed: {exc}\n"


def _ports_report() -> str:
    if sys.platform != "win32":
        return "ports: Windows only\n"
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=_no_window(),
        )
        lines = [
            ln
            for ln in (result.stdout or "").splitlines()
            if ":8000" in ln or ":3000" in ln
        ]
        return "\n".join(lines) + ("\n" if lines else "(no listeners on :8000 / :3000)\n")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"ports report failed: {exc}\n"


def _py_spy_dump(pid: int) -> str:
    commands = [
        ["py-spy", "dump", "--pid", str(pid)],
        ["py", "-m", "py_spy", "dump", "--pid", str(pid)],
    ]
    for cmd in commands:
        if shutil.which(cmd[0]) is None and cmd[0] == "py-spy":
            continue
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=45,
                creationflags=_no_window(),
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        body = (result.stdout or "") + (result.stderr or "")
        if body.strip():
            return body
    return (
        "py-spy недоступен.\n"
        "Если окно зависло: Диспетчер задач → Genesis.exe → Создать дамп файла.\n"
        "Для следующего раза (до зависания): pip install py-spy\n"
    )


def _runtime_block(root: Path | None) -> str:
    try:
        from launcher.runtime_diagnostics import format_runtime_diagnostics

        return format_runtime_diagnostics(root)
    except Exception as exc:
        return f"runtime diagnostics unavailable: {exc}\n"


def collect_launcher_diagnostics(
    root: Path | None = None,
    *,
    target_pid: int | None = None,
) -> Path:
    """Write diagnostics bundle; returns output directory path."""
    root_path = paths.find_project_root(root)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = root_path / "diagnostics" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    log_dir = paths.log_dir(root_path)
    launcher_log = log_dir / "genesis_launcher.log"

    pids = [target_pid] if target_pid else _find_genesis_pids()
    if not pids and os.getpid():
        pids = [os.getpid()]

    summary_lines = [
        f"collected_at: {datetime.now().isoformat(timespec='seconds')}",
        f"build_id: {build_info.BUILD_ID}",
        f"frozen: {getattr(sys, 'frozen', False)}",
        f"genesis_pids: {pids or 'none'}",
        "",
    ]
    (out_dir / "summary.txt").write_text("\n".join(summary_lines), encoding="utf-8")

    (out_dir / "genesis_launcher.log").write_text(
        _tail_text(launcher_log, 30), encoding="utf-8"
    )
    (out_dir / "processes.txt").write_text(_process_report(), encoding="utf-8")
    (out_dir / "ports.txt").write_text(_ports_report(), encoding="utf-8")
    (out_dir / "runtime.txt").write_text(_runtime_block(root_path), encoding="utf-8")

    stack_parts: list[str] = []
    for pid in pids:
        stack_parts.append(f"=== py-spy dump pid={pid} ===\n")
        stack_parts.append(_py_spy_dump(pid))
    (out_dir / "stack.txt").write_text("".join(stack_parts), encoding="utf-8")

    readme = (
        "Virtus Core — пакет диагностики\n"
        f"Папка: {out_dir}\n\n"
        "Файлы:\n"
        "  summary.txt       — время, build, PID\n"
        "  genesis_launcher.log — последние 30 строк журнала\n"
        "  processes.txt     — Genesis / python / node\n"
        "  ports.txt         — :8000 и :3000\n"
        "  runtime.txt       — Python, backend, frontend\n"
        "  stack.txt         — стек потоков (py-spy) или инструкция\n\n"
        "При зависании: не закрывайте Genesis.exe до сбора этого пакета.\n"
    )
    (out_dir / "README.txt").write_text(readme, encoding="utf-8")

    try:
        append_log(f"Diagnostics bundle saved: {out_dir}")
    except OSError:
        pass

    return out_dir


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Collect Virtus Core Launcher diagnostics")
    parser.add_argument("--pid", type=int, default=None, help="Genesis.exe PID (optional)")
    parser.add_argument("--root", type=str, default=None, help="Project root (optional)")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else None
    out = collect_launcher_diagnostics(root, target_pid=args.pid)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
