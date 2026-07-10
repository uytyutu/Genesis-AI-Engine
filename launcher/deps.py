"""Check Python, Node.js and project dependencies."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
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

    from launcher.process_cleanup import stop_frontend_listeners

    stop_frontend_listeners(root, managed)
    nxt = frontend_dir(root) / ".next"
    if nxt.exists():
        shutil.rmtree(nxt, ignore_errors=True)


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
    """Run `npm run build` — creates .next/routes-manifest.json for production start."""
    npm_cmd = find_npm()
    if not npm_cmd:
        return False, "Node.js / npm не найдены."

    fe = frontend_dir(root)
    if not (fe / "package.json").exists():
        return False, "package.json не найден в dashboard/frontend"

    clear_frontend_build(root, managed=managed)

    if on_progress:
        on_progress("Сборка Mission Control… (~1–2 мин)")

    build_log = log_dir(root) / "frontend_build.log"
    build_log.parent.mkdir(parents=True, exist_ok=True)
    with build_log.open("a", encoding="utf-8") as log_handle:
        log_handle.write("\n--- npm run build ---\n")
        log_handle.flush()
        try:
            result = subprocess.run(
                [npm_cmd, "run", "build"],
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
                "Сборка Mission Control заняла слишком много времени.\n"
                "См. launcher/logs/frontend_build.log",
            )

    if result.returncode != 0:
        tail = ""
        try:
            tail = build_log.read_text(encoding="utf-8", errors="replace")[-1500:]
        except OSError:
            pass
        detail = tail.splitlines()[-4:] if tail else []
        extra = "\n".join(detail) if detail else "См. launcher/logs/frontend_build.log"
        return False, f"Не удалось собрать Mission Control (npm run build).\n{extra}"

    if not frontend_build_ready(root):
        return (
            False,
            "Сборка завершилась, но .next/routes-manifest.json не найден.\n"
            "См. launcher/logs/frontend_build.log",
        )
    from launcher.log_util import append_log

    append_log(
        "Development build complete — после CEO PASS выполните Activate Stable Release"
    )
    return True, "Mission Control собран (npm run build)"


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
