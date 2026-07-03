"""Check Python, Node.js and project dependencies."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from launcher.paths import backend_dir, frontend_dir, log_dir


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


def clear_frontend_build(root: Path | None = None) -> None:
    import shutil

    nxt = frontend_dir(root) / ".next"
    if nxt.exists():
        shutil.rmtree(nxt, ignore_errors=True)


@dataclass
class DepStatus:
    python_ok: bool
    python_version: str
    python_cmd: str | None
    node_ok: bool
    node_version: str
    node_cmd: str | None
    npm_ok: bool
    npm_cmd: str | None
    backend_deps_ok: bool
    frontend_deps_ok: bool
    issues: list[str]


def find_python() -> str | None:
    if not getattr(sys, "frozen", False):
        return sys.executable
    for cmd in ("py", "python", "python3"):
        if shutil.which(cmd):
            return cmd
    return None


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
    python_cmd = find_python()
    python_ok = python_cmd is not None
    python_version = _run_version([python_cmd, "--version"]) if python_cmd else ""
    if not python_ok:
        issues.append("Python не найден на компьютере")

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
    fe = frontend_dir(root)
    backend_deps_ok = (be / "app" / "main.py").exists()
    if not backend_deps_ok:
        issues.append("Backend не найден в проекте")

    frontend_deps_ok = frontend_deps_ready(root)
    if node_ok and not frontend_deps_ok:
        issues.append("Mission Control ещё не установлен — Genesis установит автоматически")

    return DepStatus(
        python_ok=python_ok,
        python_version=python_version,
        python_cmd=python_cmd,
        node_ok=node_ok,
        node_version=node_version,
        node_cmd=node_cmd,
        npm_ok=npm_ok,
        npm_cmd=npm_cmd,
        backend_deps_ok=backend_deps_ok,
        frontend_deps_ok=frontend_deps_ok,
        issues=issues,
    )


def install_backend_deps(root: Path | None = None) -> tuple[bool, str]:
    deps = check_dependencies(root)
    if not deps.python_cmd:
        return False, "Python не найден"
    be = backend_dir(root)
    req = be / "requirements.txt"
    if not req.exists():
        return False, "requirements.txt не найден"
    result = subprocess.run(
        [deps.python_cmd, "-m", "pip", "install", "-r", str(req), "-q"],
        cwd=be,
        capture_output=True,
        text=True,
        creationflags=_no_window(),
    )
    if result.returncode != 0:
        return False, result.stderr.strip() or "Ошибка установки Python-зависимостей"
    return True, "Python-зависимости установлены"


def ensure_frontend_ready(root: Path | None = None, *, for_production: bool = False) -> tuple[bool, str]:
    """Install npm packages; production builds only when for_production=True."""
    npm_cmd = find_npm()
    if not npm_cmd:
        return (
            False,
            "Node.js не найден.\n\n"
            "Нажмите «Запустить» в Genesis — откроется окно с автоматической установкой.",
        )

    if not frontend_deps_ready(root):
        ok, msg = install_frontend_deps(root)
        if not ok:
            return False, msg

    if not for_production:
        return True, "Mission Control готов"

    if frontend_build_ready(root) and frontend_build_integrity(root):
        return True, "Mission Control готов"

    if frontend_build_ready(root) and not frontend_build_integrity(root):
        clear_frontend_build(root)

    ok, msg = build_frontend(root)
    if not ok:
        return False, msg
    return True, "Mission Control собран и готов"


def build_frontend(root: Path | None = None) -> tuple[bool, str]:
    """Run `npm run build` — creates .next/routes-manifest.json for production start."""
    npm_cmd = find_npm()
    if not npm_cmd:
        return False, "Node.js / npm не найдены."

    fe = frontend_dir(root)
    if not (fe / "package.json").exists():
        return False, "package.json не найден в dashboard/frontend"

    clear_frontend_build(root)

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
    return True, "Mission Control собран (npm run build)"


def install_frontend_deps(root: Path | None = None) -> tuple[bool, str]:
    deps = check_dependencies(root)
    npm_cmd = deps.npm_cmd or find_npm()
    if not npm_cmd:
        return False, "Node.js / npm не найдены. Запустите Genesis — установка в один клик."
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
