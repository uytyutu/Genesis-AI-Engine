"""Automatic desktop shortcut + Windows icon refresh — no CEO PowerShell."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from launcher.branding import BRAND_NAME, ico_path
from launcher.log_util import append_log
from launcher import paths

STAMP_FILE = "desktop_identity_stamp.json"


@dataclass
class IdentityResult:
    ok: bool
    message: str
    shortcut_path: str = ""
    refreshed_cache: bool = False


def _no_window() -> int:
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return 0


def _exe_path(root: Path) -> Path | None:
    for name in ("Genesis.exe", "Genesis Launcher.exe"):
        candidate = root / "dist" / name
        if candidate.is_file():
            return candidate
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return None


def _shortcut_path() -> Path:
    desktop = Path.home() / "Desktop"
    if not desktop.is_dir():
        import os

        desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
    return desktop / "Virtus Core.lnk"


def _identity_stamp(root: Path) -> str:
    exe = _exe_path(root)
    ico = ico_path()
    parts: list[str] = []
    if exe and exe.is_file():
        parts.append(f"exe:{exe.stat().st_mtime_ns}:{exe.stat().st_size}")
    if ico.is_file():
        parts.append(f"ico:{ico.stat().st_mtime_ns}:{ico.stat().st_size}")
    return "|".join(parts) or "unknown"


def _stamp_path(root: Path) -> Path:
    return paths.memory_dir(root) / STAMP_FILE


def _load_stamp(root: Path) -> str:
    path = _stamp_path(root)
    if not path.is_file():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(data.get("stamp", ""))
    except (OSError, json.JSONDecodeError):
        return ""


def _save_stamp(root: Path, stamp: str) -> None:
    path = _stamp_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"stamp": stamp}, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_hidden_ps(script: str) -> tuple[bool, str]:
    if sys.platform != "win32":
        return True, "skipped (not Windows)"
    try:
        result = subprocess.run(
            [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-WindowStyle",
                "Hidden",
                "-NoProfile",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            creationflags=_no_window(),
            timeout=120,
        )
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        if result.returncode != 0:
            return False, err or out or f"exit {result.returncode}"
        return True, out
    except Exception as exc:
        return False, str(exc)


def _create_shortcut_ps(root: Path, exe: Path) -> tuple[bool, str]:
    shortcut = _shortcut_path()
    root_s = str(root.resolve()).replace("'", "''")
    exe_s = str(exe.resolve()).replace("'", "''")
    sc_s = str(shortcut.resolve()).replace("'", "''")
    script = f"""
$ErrorActionPreference = 'Stop'
$Wsh = New-Object -ComObject WScript.Shell
$Shortcut = $Wsh.CreateShortcut('{sc_s}')
$Shortcut.TargetPath = '{exe_s}'
$Shortcut.WorkingDirectory = '{root_s}'
$Shortcut.Description = 'Virtus Core — Vector Intelligent AI Assistant'
$Shortcut.IconLocation = '{exe_s},0'
$Shortcut.Save()
Write-Output 'ok'
"""
    return _run_hidden_ps(script)


def _soft_icon_refresh() -> None:
    if sys.platform != "win32":
        return
    import shutil

    ie4 = shutil.which("ie4uinit.exe")
    if ie4:
        try:
            subprocess.run([ie4, "-show"], creationflags=_no_window(), timeout=15)
        except OSError:
            pass


def _hard_icon_refresh() -> tuple[bool, str]:
    """Clear Explorer icon cache + restart Explorer — once after exe/ico change."""
    if sys.platform != "win32":
        return True, "skipped"
    script = r"""
$ErrorActionPreference = 'SilentlyContinue'
$cache = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Explorer'
Get-ChildItem $cache -Filter 'iconcache*' -Force | Remove-Item -Force
Get-ChildItem $cache -Filter 'thumbcache_*.db' -Force | Remove-Item -Force
Stop-Process -Name explorer -Force
Start-Sleep -Seconds 2
Start-Process explorer.exe
Write-Output 'cache-cleared'
"""
    return _run_hidden_ps(script)


def ensure_desktop_identity(
    root: Path | None = None,
    *,
    force_cache: bool = False,
    skip_hard_cache: bool = False,
) -> IdentityResult:
    """
    Runs automatically on Genesis launch and after build.
    CEO never runs PowerShell — Genesis fixes shortcut + icon cache itself.
    """
    if sys.platform != "win32":
        return IdentityResult(True, "Desktop identity: not Windows")

    root = root or paths.find_project_root()
    exe = _exe_path(root)
    if exe is None or not exe.is_file():
        return IdentityResult(False, f"{BRAND_NAME} не найден — пересоберите launcher\\build.ps1")

    ok, msg = _create_shortcut_ps(root, exe)
    if not ok:
        append_log(f"Desktop shortcut failed: {msg}")
        return IdentityResult(False, f"Не удалось обновить ярлык: {msg}")

    shortcut = str(_shortcut_path())
    append_log(f"Desktop shortcut updated: {shortcut} icon={exe},0")

    stamp = _identity_stamp(root)
    prev = _load_stamp(root)
    stamp_changed = stamp != prev
    refreshed_cache = False

    _soft_icon_refresh()

    if not skip_hard_cache and (force_cache or stamp_changed):
        ok_cache, cache_msg = _hard_icon_refresh()
        refreshed_cache = ok_cache
        if ok_cache:
            append_log("Windows icon cache refreshed (Explorer restarted once)")
            _save_stamp(root, stamp)
        else:
            append_log(f"Icon cache refresh partial: {cache_msg}")
            _save_stamp(root, stamp)

    return IdentityResult(
        ok=True,
        message="Ярлык и иконка обновлены автоматически",
        shortcut_path=shortcut,
        refreshed_cache=refreshed_cache,
    )


def ensure_desktop_identity_async(root: Path | None = None) -> None:
    """Background shortcut refresh only — Explorer hard restart is build-time only."""

    def _worker() -> None:
        try:
            ensure_desktop_identity(root, skip_hard_cache=True)
        except Exception as exc:
            append_log(f"Desktop identity async error: {exc}")

    import threading

    threading.Thread(target=_worker, daemon=True).start()
