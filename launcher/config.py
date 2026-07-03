"""Launcher settings stored in project memory folder."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from launcher import paths


@dataclass
class LauncherConfig:
    first_run_complete: bool = False
    owner_name: str = "Владелец"
    auto_open_browser: bool = True
    project_root: str = ""
    last_launch_at: str = ""
    daily_goal: str = "Создать первый цифровой продукт."
    goals: list[str] = field(default_factory=lambda: ["earnings"])
    product_interests: list[str] = field(
        default_factory=lambda: ["landing", "shop", "telegram", "saas"]
    )
    company_founded_at: str = ""
    keep_running_on_close: bool = True
    auto_start_on_open: bool = True

    @classmethod
    def load(cls) -> LauncherConfig:
        path = _config_path()
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        if "goals" not in known:
            known["goals"] = ["earnings"]
        if "product_interests" not in known:
            known["product_interests"] = ["landing", "shop", "telegram", "saas"]
        return cls(**known)

    def save(self) -> None:
        path = _config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")

    def touch_launch(self) -> None:
        self.last_launch_at = datetime.now(timezone.utc).isoformat()
        self.save()


def _config_path() -> Path:
    return paths.memory_dir() / "launcher_config.json"
