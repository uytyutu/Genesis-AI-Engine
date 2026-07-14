"""Check Python, Node.js and project dependencies."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from launcher.paths import backend_dir, frontend_dir, log_dir
from launcher.python_runtime import (
    SUPPORTED_PYTHON_LABEL,
    backend_python_argv,
    resolve_any_python,
    resolve_backend_python,
    unsupported_python_message,
)


def frontend_deps_ready(root: Path | None = None) -> bool:
    """True when Next.js and core packages are present — not just an empty node_modules/."""
    fe = frontend_dir(root)
    nm = fe / "node_modules"
    return nm.is_dir() and (nm / "next").is_dir() and (nm / "react").is_dir()


def frontend_build_marker(root: Path | None = None) -> Path:
    return frontend_dir(root) / ".next" / "routes-manifest.json"


def frontend_build_ready(root: Path | None = None) -> bool:
    """Production build exists — required for `next start` and stable Genesis.exe launches."""
    return frontend_build_marker(root).is_file()


def frontend_build_integrity(root: Path | None = None) -> bool:
    """True when .next is a complete production build, not a stale/partial cache."""
    if not frontend_build_ready(root):
        return False
    nxt = frontend_dir(root) / ".next"
    required = (
        nxt / "BUILD_ID",
        nxt / "routes-manifest.json",
        nxt / "server" / "pages-manifest.json",
        nxt / "server" / "app" / "page.js",
    )
    return all(p.is_file() for p in required)


_FRONTEND_SOURCE_SUFFIXES = frozenset({".tsx", ".ts", ".json", ".css", ".scss"})


def frontend_source_stamp(root: Path | None = None) -> float:
    """Newest mtime among customer-facing frontend sources (app, locales, public)."""
    fe = frontend_dir(root)
    newest = 0.0
    for rel in ("app", "locales", "public"):
        base = fe / rel
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in _FRONTEND_SOURCE_SUFFIXES:
                continue
            try:
                newest = max(newest, path.stat().st_mtime)
            except OSError:
                continue
    return newest


def frontend_build_stale(root: Path | None = None) -> bool:
    """True when source changed after the last production build."""
    if not frontend_build_ready(root):
        return False
    build_id = frontend_dir(root) / ".next" / "BUILD_ID"
    try:
        build_mtime = build_id.stat().st_mtime
    except OSError:
        return True
    return frontend_source_stamp(root) > build_mtime + 1.0


def clear_frontend_build(root: Path | None = None, *, managed=None) -> None:
    """Remove .next only after stopping Frontend — never delete artifacts under a live server."""
    import shutil

    from launcher.process_cleanup import stop_frontend_listeners, wait_port_free

    stop_frontend_listeners(root, managed)
    wait_port_free(3000, timeout=12.0)
    nxt = frontend_dir(root) / ".next"
    if not nxt.exists():
        return
    for attempt in range(4):
        try:
            shutil.rmtree(nxt)
            return
        except OSError:
            if attempt >= 3:
                shutil.rmtree(nxt, ignore_errors=True)
                return
            stop_frontend_listeners(root, managed)
            time.sleep(0.8 + attempt * 0.4)


_BACKUP_DIR_NAME = ".next.launcher_backup"


def backup_frontend_build(root: Path | None = None) -> bool:
    """Snapshot working .next before Development Update — restore if build fails."""
    import shutil

    if not frontend_build_ready(root) or not frontend_build_integrity(root):
        return False
    fe = frontend_dir(root)
    src = fe / ".next"
    dst = fe / _BACKUP_DIR_NAME
    if dst.exists():
        shutil.rmtree(dst, ignore_errors=True)
    try:
        shutil.copytree(src, dst)
        from launcher.log_util import append_log

        append_log("Development Update: backed up .next before rebuild")
        return True
    except OSError:
        return False


def restore_frontend_build_backup(root: Path | None = None) -> bool:
    """Restore last good .next after failed Development Update."""
    import shutil

    fe = frontend_dir(root)
    bak = fe / _BACKUP_DIR_NAME
    nxt = fe / ".next"
    if not bak.is_dir():
        return False
    if nxt.exists():
        shutil.rmtree(nxt, ignore_errors=True)
    try:
        shutil.copytree(bak, nxt)
        from launcher.log_util import append_log

        append_log("Development Update failed — restored .next from launcher backup")
        return frontend_build_ready(root)
    except OSError:
        return False


def discard_frontend_build_backup(root: Path | None = None) -> None:
    import shutil

    bak = frontend_dir(root) / _BACKUP_DIR_NAME
    if bak.exists():
        shutil.rmtree(bak, ignore_errors=True)


def _run_npm_build(
    root: Path | None,
    *,
    npm_cmd: str,
    on_progress: Callable[[str], None] | None,
    build_log: Path,
    timeout_sec: float = 900.0,
) -> int:
    """Run npm run build; return exit code."""
    fe = frontend_dir(root)
    with build_log.open("a", encoding="utf-8") as log_handle:
        log_handle.write("\n--- npm run build ---\n")
        log_handle.flush()
        proc = subprocess.Popen(
            [npm_cmd, "run", "build"],
            cwd=fe,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            shell=False,
            env={**os.environ, "PATH": augmented_path()},
            creationflags=_no_window(),
        )
        started = time.monotonic()
        last_progress = -1
        while proc.poll() is None:
            elapsed = int(time.monotonic() - started)
            if on_progress and elapsed >= 10 and elapsed // 10 != last_progress:
                last_progress = elapsed // 10
                minutes, seconds = divmod(elapsed, 60)
                on_progress(f"Сборка Mission Control… ({minutes}:{seconds:02d})")
            if elapsed > timeout_sec:
                proc.kill()
                proc.wait(timeout=10)
                return 124
            time.sleep(0.5)
        return int(proc.returncode or 0)


@dataclass
class DepStatus:
    python_ok: bool
    python_version: str
    python_cmd: str | None
    python_supported: bool
    backend_packages_ok: bool
    node_ok: bool
    node_version: str
    node_cmd: str | None
    npm_ok: bool
    npm_cmd: str | None
    backend_deps_ok: bool
    frontend_deps_ok: bool
    issues: list[str]


def find_python() -> str | None:
    """Backend Python command for display — prefers supported 3.12."""
    argv = backend_python_argv()
    if argv:
        return " ".join(argv)
    detected = resolve_any_python()
    return detected.display_cmd if detected else None


def _parse_requirements_file(req_path: Path) -> list[tuple[str, str | None]]:
    specs: list[tuple[str, str | None]] = []
    for raw in req_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "==" in line:
            name, version = line.split("==", 1)
            name = name.split("[", 1)[0].strip().lower().replace("_", "-")
            specs.append((name, version.strip()))
        else:
            name = line.split("[", 1)[0].strip().lower().replace("_", "-")
            specs.append((name, None))
    return specs


def backend_requirements_satisfied(
    python_argv: list[str],
    root: Path | None = None,
) -> tuple[bool, str]:
    """True when pinned backend packages are importable at required versions."""
    req = backend_dir(root) / "requirements.txt"
    if not req.is_file():
        return False, "requirements.txt не найден"
    specs = _parse_requirements_file(req)
    if not specs:
        return True, ""
    payload = json.dumps({name: ver for name, ver in specs})
    script = f"""
import importlib.metadata as md
import json
import sys
specs = json.loads({payload!r})
for name, want in specs.items():
    try:
        got = md.version(name)
    except md.PackageNotFoundError:
        print(f"missing:{{name}}")
        sys.exit(2)
    if want and got != want:
        print(f"version:{{name}}:{{got}}!={{want}}")
        sys.exit(3)
"""
    result = subprocess.run(
        [*python_argv, "-c", script],
        capture_output=True,
        text=True,
        creationflags=_no_window(),
    )
    if result.returncode == 0:
        return True, ""
    detail = (result.stdout or result.stderr).strip().splitlines()
    return False, detail[-1] if detail else "зависимости не совпадают с requirements.txt"


def ensure_backend_deps(
    root: Path | None = None,
    *,
    force: bool = False,
) -> tuple[bool, str]:
    """Install backend requirements only when missing, wrong version, or force=True."""
    return install_backend_deps(root, force=force)


def install_backend_deps(
    root: Path | None = None,
    *,
    force: bool = False,
) -> tuple[bool, str]:
    runtime = resolve_backend_python()
    if runtime is None:
        return False, unsupported_python_message(resolve_any_python())

    if not force:
        ok, reason = backend_requirements_satisfied(runtime.argv, root)
        if ok:
            return True, "Python-зависимости уже установлены"

    be = backend_dir(root)
    req = be / "requirements.txt"
    if not req.exists():
        return False, "requirements.txt не найден"
    result = subprocess.run(
        [*runtime.argv, "-m", "pip", "install", "-r", str(req), "-q"],
        cwd=be,
        capture_output=True,
        text=True,
        creationflags=_no_window(),
    )
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip() or "Ошибка установки Python-зависимостей"
        if "pydantic-core" in err or "link.exe" in err:
            return (
                False,
                f"{unsupported_python_message(runtime)}\n\n"
                f"Подробности pip:\n{err[-1200:]}",
            )
        return False, err
    return True, "Python-зависимости установлены"
def _node_install_dirs() -> list[Path]:
    dirs: list[Path] = []
    for key in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(key)
        if base:
            dirs.append(Path(base) / "nodejs")
    local = os.environ.get("LOCALAPPDATA")
    if local:
        dirs.append(Path(local) / "Programs" / "nodejs")
    appdata = os.environ.get("APPDATA")
    if appdata:
        dirs.append(Path(appdata) / "npm")
    return dirs


def find_node() -> str | None:
    found = shutil.which("node")
    if found:
        return found
    for folder in _node_install_dirs():
        candidate = folder / "node.exe"
        if candidate.exists():
            return str(candidate)
    return None


def find_npm() -> str | None:
    found = shutil.which("npm")
    if found:
        return found
    for folder in _node_install_dirs():
        for name in ("npm.cmd", "npm.exe"):
            candidate = folder / name
            if candidate.exists():
                return str(candidate)
    node = find_node()
    if node:
        sibling = Path(node).parent / "npm.cmd"
        if sibling.exists():
            return str(sibling)
    return None


def augmented_path() -> str:
    """GUI apps on Windows often miss Node in PATH — prepend common install dirs."""
    extra: list[str] = []
    node = find_node()
    if node:
        extra.append(str(Path(node).parent))
    for folder in _node_install_dirs():
        extra.append(str(folder))
    current = os.environ.get("PATH", "")
    merged = os.pathsep.join(dict.fromkeys(extra + [current]))
    return merged


def _run_version(cmd: list[str]) -> str:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=_no_window(),
            env={**os.environ, "PATH": augmented_path()},
        )
        if result.returncode == 0:
            return result.stdout.strip() or result.stderr.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return ""


def _no_window() -> int:
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return 0


def check_dependencies(root: Path | None = None) -> DepStatus:
    issues: list[str] = []
    runtime = resolve_backend_python()
    detected = resolve_any_python() if runtime is None else None
    python_supported = runtime is not None
    python_ok = python_supported
    python_cmd = runtime.display_cmd if runtime else (detected.display_cmd if detected else None)
    python_version = runtime.version_text if runtime else (detected.version_text if detected else "")
    if not python_supported:
        issues.append(
            f"Нужен Python {SUPPORTED_PYTHON_LABEL}. "
            + (
                f"Сейчас: {detected.version_text}."
                if detected
                else "Python не найден."
            )
        )

    backend_packages_ok = False
    if runtime is not None:
        backend_packages_ok, pkg_reason = backend_requirements_satisfied(runtime.argv, root)
        if not backend_packages_ok and pkg_reason:
            issues.append(f"Python-пакеты: {pkg_reason}")

    node_cmd = find_node()
    node_ok = node_cmd is not None
    node_version = _run_version([node_cmd, "--version"]) if node_cmd else ""
    if not node_ok:
        issues.append("Node.js — нажмите «Запустить» для автоматической установки")

    npm_cmd = find_npm()
    npm_ok = npm_cmd is not None
    if node_ok and not npm_ok:
        issues.append("npm не найден")

    be = backend_dir(root)
    backend_deps_ok = (be / "app" / "main.py").exists()
    if not backend_deps_ok:
        issues.append("Backend не найден в проекте")

    frontend_deps_ok = frontend_deps_ready(root)
    if node_ok and not frontend_deps_ok:
        issues.append("Mission Control ещё не установлен — Virtus Core установит автоматически")

    return DepStatus(
        python_ok=python_ok,
        python_version=python_version,
        python_cmd=python_cmd,
        python_supported=python_supported,
        backend_packages_ok=backend_packages_ok,
        node_ok=node_ok,
        node_version=node_version,
        node_cmd=node_cmd,
        npm_ok=npm_ok,
        npm_cmd=npm_cmd,
        backend_deps_ok=backend_deps_ok,
        frontend_deps_ok=frontend_deps_ok,
        issues=issues,
    )


def ensure_frontend_ready(
    root: Path | None = None,
    *,
    for_production: bool = False,
    managed=None,
    build_policy: str = "rebuild_on_stale",
    on_build_progress: Callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """Install npm packages; production builds only when for_production=True.

    build_policy:
      launch_stable — use last good .next; never rebuild only because sources are newer
      rebuild_now   — explicit Development Update (npm run build)
      rebuild_on_stale — legacy auto-rebuild when sources changed (avoid for CEO path)
    """
    from launcher.frontend_build_policy import POLICY_LAUNCH_STABLE, POLICY_REBUILD_NOW

    npm_cmd = find_npm()
    if not npm_cmd:
        return (
            False,
            "Node.js не найден.\n\n"
            "Нажмите «Запустить» в Virtus Core — откроется окно с автоматической установкой.",
        )

    if not frontend_deps_ready(root):
        ok, msg = install_frontend_deps(root)
        if not ok:
            return False, msg

    if not for_production:
        return True, "Mission Control готов"

    policy = build_policy
    if policy not in (POLICY_LAUNCH_STABLE, POLICY_REBUILD_NOW, "rebuild_on_stale"):
        policy = "rebuild_on_stale"

    if policy == POLICY_LAUNCH_STABLE:
        from launcher.stable_release import ensure_active_release_deployed

        deployed_ok, deployed_msg = ensure_active_release_deployed(root)
        if not deployed_ok:
            return False, (
                f"Не удалось развернуть стабильный релиз ({deployed_msg}).\n"
                "Откройте режим восстановления или пересоберите в «Разработка»."
            )
        if frontend_build_ready(root) and frontend_build_integrity(root):
            from launcher.log_util import append_log

            if frontend_build_stale(root):
                append_log(
                    "Normal Launch: using active Stable Release (sources changed — no auto-rebuild)"
                )
            else:
                append_log(f"Normal Launch: Stable Release ready ({deployed_msg})")
            return True, "Mission Control готов (стабильный релиз)"
        if frontend_build_ready(root) and not frontend_build_integrity(root):
            return (
                False,
                "Production повреждён.\n"
                "Используйте режим восстановления или пересборку в «Разработка».",
            )
        return (
            False,
            "Стабильный релиз не найден.\n"
            "Режим «Разработка» → сборка → CEO PASS → Activate Stable Release.",
        )

    if policy == POLICY_REBUILD_NOW:
        ok, msg = build_frontend(root, managed=managed, on_progress=on_build_progress)
        if not ok:
            return False, msg
        return True, "Mission Control собран (Development Update)"

    if frontend_build_ready(root) and frontend_build_integrity(root) and not frontend_build_stale(root):
        return True, "Mission Control готов"

    if policy == "rebuild_on_stale" and frontend_build_ready(root) and frontend_build_stale(root):
        from launcher.log_util import append_log

        append_log("Frontend source newer than .next — rebuilding production build")
        clear_frontend_build(root, managed=managed)

    if frontend_build_ready(root) and not frontend_build_integrity(root):
        clear_frontend_build(root, managed=managed)

    ok, msg = build_frontend(root, managed=managed, on_progress=on_build_progress)
    if not ok:
        return False, msg
    return True, "Mission Control собран и готов"


def build_frontend(
    root: Path | None = None,
    *,
    managed=None,
    on_progress: Callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """Development Update — safe rebuild with backup, retry, and parsed errors."""
    from launcher.build_log_parse import extract_build_failure

    npm_cmd = find_npm()
    if not npm_cmd:
        return False, "Node.js / npm не найдены."

    fe = frontend_dir(root)
    if not (fe / "package.json").exists():
        return False, "package.json не найден в dashboard/frontend"

    backed_up = backup_frontend_build(root)
    build_log = log_dir(root) / "frontend_build.log"
    build_log.parent.mkdir(parents=True, exist_ok=True)

    def _fail_message(code: int, *, restored: bool) -> str:
        headline, details = extract_build_failure(root)
        lines = [
            "Не удалось собрать Mission Control (npm run build).",
            "",
            f"Причина: {headline}",
        ]
        if details:
            lines.append("")
            lines.extend(details[:8])
        if code == 124:
            lines[2] = "Причина: таймаут сборки (>15 мин)"
        lines.append("")
        lines.append("См. launcher/logs/frontend_build.log")
        if restored:
            lines.append("")
            lines.append(
                "✓ Предыдущий рабочий релиз восстановлен автоматически.\n"
                "Нажмите «Запустить» — откроется последний Stable Release."
            )
        return "\n".join(lines)

    def _attempt(label: str, *, clean: bool) -> int:
        if on_progress:
            on_progress(label)
        if clean:
            clear_frontend_build(root, managed=managed)
        return _run_npm_build(
            root,
            npm_cmd=npm_cmd,
            on_progress=on_progress,
            build_log=build_log,
        )

    # 1) Incremental build (keep .next) — fast path after small edits
    code = _attempt("Сборка Mission Control… (~1–2 мин)", clean=False)
    if code == 0 and frontend_build_ready(root):
        discard_frontend_build_backup(root)
        from launcher.build_failure_report import clear_last_build_failure
        from launcher.log_util import append_log

        clear_last_build_failure(root)
        append_log("Development Update: incremental build OK")
        return True, "Mission Control собран (Development Update)"

    # 2) Clean rebuild
    code = _attempt("Сборка Mission Control… повтор с чистым .next", clean=True)
    if code == 0 and frontend_build_ready(root):
        discard_frontend_build_backup(root)
        from launcher.build_failure_report import clear_last_build_failure
        from launcher.log_util import append_log

        clear_last_build_failure(root)
        append_log("Development build complete — после CEO PASS выполните Activate Stable Release")
        return True, "Mission Control собран (npm run build)"

    restored = False
    if backed_up:
        restored = restore_frontend_build_backup(root)

    headline, details = extract_build_failure(root)
    from launcher.build_failure_report import record_build_failure

    record = record_build_failure(
        root,
        exit_code=code,
        restored=restored,
        headline=headline,
        details=details,
    )
    fail_msg = _fail_message(code, restored=restored)
    fail_msg += f"\n\nОтчёт сохранён: Build #{record.build_number} — откройте на главном экране Launcher."
    return False, fail_msg


def install_frontend_deps(root: Path | None = None) -> tuple[bool, str]:
    deps = check_dependencies(root)
    npm_cmd = deps.npm_cmd or find_npm()
    if not npm_cmd:
        return False, "Node.js / npm не найдены. Запустите Virtus Core — установка в один клик."
    fe = frontend_dir(root)
    if not (fe / "package.json").exists():
        return False, "package.json не найден в dashboard/frontend"

    npm_log = log_dir(root) / "npm_install.log"
    npm_log.parent.mkdir(parents=True, exist_ok=True)
    with npm_log.open("a", encoding="utf-8") as log_handle:
        log_handle.write("\n--- npm install ---\n")
        log_handle.flush()
        try:
            result = subprocess.run(
                [npm_cmd, "install", "--no-fund", "--no-audit"],
                cwd=fe,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                shell=False,
                env={**os.environ, "PATH": augmented_path()},
                creationflags=_no_window(),
                timeout=900,
            )
        except subprocess.TimeoutExpired:
            return (
                False,
                "Установка Mission Control заняла слишком много времени.\n"
                "Проверьте интернет и launcher/logs/npm_install.log",
            )

    if result.returncode != 0:
        return (
            False,
            "Не удалось установить Mission Control.\n"
            "Проверьте интернет и launcher/logs/npm_install.log",
        )
    if not frontend_deps_ready(root):
        return False, "Установка завершилась, но зависимости неполные. Нажмите «Установить Mission Control» ещё раз."
    return True, "Mission Control установлен"
