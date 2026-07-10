"""Launch Architecture v2 — Пользователь vs Разработка (UX only, not Git control)."""

from __future__ import annotations

from launcher.config import LauncherConfig

LAUNCH_MODE_OWNER = "owner"
LAUNCH_MODE_DEVELOPMENT = "development"

_MODE_LABELS = {
    LAUNCH_MODE_OWNER: "CEO — открыть компанию",
    LAUNCH_MODE_DEVELOPMENT: "Разработка",
}

_MODE_HINTS = {
    LAUNCH_MODE_OWNER: (
        "Ежедневная работа с Virtus Core — быстрый запуск без пересборки. "
        "Изменения кода → отдельное обновление по вашему выбору."
    ),
    LAUNCH_MODE_DEVELOPMENT: (
        "Development Mode: Cursor, сборки, тесты, миграции. "
        "Launcher пересобирает Mission Control при изменениях исходников."
    ),
}


def normalize_launch_mode(value: str | None) -> str:
    if (value or "").strip().lower() == LAUNCH_MODE_DEVELOPMENT:
        return LAUNCH_MODE_DEVELOPMENT
    return LAUNCH_MODE_OWNER


def load_launch_mode() -> str:
    cfg = LauncherConfig.load()
    return normalize_launch_mode(getattr(cfg, "launch_mode", LAUNCH_MODE_OWNER))


def launch_mode_label(mode: str | None = None) -> str:
    return _MODE_LABELS.get(normalize_launch_mode(mode), _MODE_LABELS[LAUNCH_MODE_OWNER])


def launch_mode_hint(mode: str | None = None) -> str:
    return _MODE_HINTS.get(normalize_launch_mode(mode), _MODE_HINTS[LAUNCH_MODE_OWNER])
