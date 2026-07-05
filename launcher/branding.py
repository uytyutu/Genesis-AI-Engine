"""Genesis Brand v1.0 Orbit Stack — launcher colors and assets."""

from __future__ import annotations

from pathlib import Path

from launcher import paths

# Synced with client/desktop/src/styles/theme.css
GENESIS_BG = "#050508"
GENESIS_PANEL = "#111118"
GENESIS_ELEVATED = "#18181f"
GENESIS_BORDER = "#27272f"
GENESIS_ACCENT = "#5b8def"
GENESIS_ACCENT_HOVER = "#4f46e5"
GENESIS_MUTED = "#8b8b9a"
GENESIS_TEXT = "#ececf1"
GENESIS_GREEN = "#34d399"
GENESIS_GREEN_HOVER = "#059669"
GENESIS_AMBER = "#fbbf24"
GENESIS_ROSE = "#fb7185"


def project_root() -> Path:
    return paths.find_project_root()


def ico_path() -> Path:
    return project_root() / "launcher" / "assets" / "genesis.ico"


def mark_png_path() -> Path:
    return project_root() / "launcher" / "assets" / "genesis-icon.png"


def load_mark_pil_image():
    """PIL image for CTkImage — paths/strings crash CustomTkinter."""
    path = mark_png_path()
    if not path.is_file():
        return None
    try:
        from PIL import Image

        with Image.open(path) as img:
            return img.copy()
    except OSError:
        return None


def apply_window_icon(window) -> None:
    """Set taskbar / title bar icon on Windows."""
    ico = ico_path()
    if not ico.exists():
        return
    try:
        window.iconbitmap(default=str(ico))
    except Exception:
        pass
