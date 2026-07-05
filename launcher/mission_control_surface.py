"""Mission Control surface — browser today, embedded WebView after Native Desktop."""

from __future__ import annotations

import os
import sys
import webbrowser
from typing import Literal

from launcher.log_util import append_log

SurfaceMode = Literal["browser", "desktop"]

SURFACE_BROWSER: SurfaceMode = "browser"
SURFACE_DESKTOP: SurfaceMode = "desktop"

_DESKTOP_HOOK = None  # Future: Tauri/WebView host registers open(url) -> bool


def register_desktop_shell(opener) -> None:
    """Native Desktop host calls this once WebView is ready (Tauri phase)."""
    global _DESKTOP_HOOK
    _DESKTOP_HOOK = opener


def resolve_surface_mode(config_surface: str | None = None) -> SurfaceMode:
    raw = (os.environ.get("GENESIS_MC_SURFACE") or config_surface or SURFACE_BROWSER).strip().lower()
    if raw == SURFACE_DESKTOP:
        return SURFACE_DESKTOP
    return SURFACE_BROWSER


def open_mission_control(url: str, *, surface: SurfaceMode | None = None) -> tuple[bool, str]:
    """Single entry point — Launcher, Kernel, and tests call only this."""
    if not url:
        return False, "URL пустой"

    mode = surface or resolve_surface_mode()
    if mode == SURFACE_DESKTOP:
        ok, err = _open_in_desktop_shell(url)
        if ok:
            return True, ""
        append_log(f"Desktop surface unavailable ({err or 'no host'}) — browser fallback")

    return _open_in_browser(url)


def _open_in_desktop_shell(url: str) -> tuple[bool, str]:
    if _DESKTOP_HOOK is not None:
        try:
            if _DESKTOP_HOOK(url):
                append_log(f"Mission Control opened in desktop shell: {url}")
                return True, ""
            return False, "desktop host returned false"
        except Exception as exc:
            append_log(f"Desktop shell open failed: {exc}")
            return False, str(exc)
    return False, "desktop shell not connected"


def _open_in_browser(url: str) -> tuple[bool, str]:
    try:
        if webbrowser.open(url, new=2):
            append_log(f"Mission Control opened via webbrowser: {url}")
            return True, ""
    except Exception as exc:
        append_log(f"webbrowser.open failed: {exc}")

    if sys.platform == "win32":
        try:
            os.startfile(url)  # type: ignore[attr-defined]
            append_log(f"Mission Control opened via os.startfile: {url}")
            return True, ""
        except OSError as exc:
            append_log(f"os.startfile failed: {exc}")
            return False, str(exc)

    return False, "Не удалось открыть браузер автоматически"
