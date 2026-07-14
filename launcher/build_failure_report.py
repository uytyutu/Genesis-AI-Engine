"""Persist last Development Update failure — CEO opens one button on next launch."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from launcher.build_log_parse import parse_build_failure
from launcher.paths import log_dir

_STORE_NAME = "last_build_failure.json"


@dataclass(frozen=True)
class BuildFailureRecord:
    build_number: int
    timestamp: str
    file: str
    line: int | None
    message: str
    headline: str
    exit_code: int
    restored: bool
    details: tuple[str, ...] = ()

    def short_summary(self) -> str:
        line_part = f"\nстрока {self.line}" if self.line else ""
        return f"Build #{self.build_number}\n{self.file}\n{self.message}{line_part}"

    def display_text(self) -> str:
        when = self.timestamp.replace("T", " ").replace("+00:00", " UTC")[:19]
        lines = [
            f"Build #{self.build_number}",
            f"Время: {when}",
            "",
            self.file,
            self.message,
        ]
        if self.line:
            lines.append(f"строка {self.line}")
        lines.extend(["", f"Причина: {self.headline}"])
        if self.exit_code == 124:
            lines[-1] = "Причина: таймаут сборки (>15 мин)"
        if self.restored:
            lines.extend(["", "✓ Предыдущий Stable Release восстановлен автоматически"])
        if self.details:
            lines.extend(["", "Детали:"])
            lines.extend(self.details[:10])
        lines.extend(["", "Полный лог: launcher/logs/frontend_build.log"])
        return "\n".join(lines)

    def button_label(self) -> str:
        short_file = self.file.split("/")[-1] if self.file else "сборка"
        return f"⚠ Последняя неудачная сборка · Build #{self.build_number} · {short_file}"


def _store_path(root: Path | None = None) -> Path:
    return log_dir(root) / _STORE_NAME


def _load_store(root: Path | None = None) -> dict:
    path = _store_path(root)
    if not path.is_file():
        return {"next_build_number": 1, "last_failure": None}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"next_build_number": 1, "last_failure": None}
    if not isinstance(data, dict):
        return {"next_build_number": 1, "last_failure": None}
    data.setdefault("next_build_number", 1)
    return data


def _save_store(root: Path | None, data: dict) -> None:
    path = _store_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_last_build_failure(root: Path | None = None) -> BuildFailureRecord | None:
    raw = _load_store(root).get("last_failure")
    if not raw or not isinstance(raw, dict):
        return None
    try:
        return BuildFailureRecord(
            build_number=int(raw["build_number"]),
            timestamp=str(raw["timestamp"]),
            file=str(raw.get("file") or "—"),
            line=int(raw["line"]) if raw.get("line") is not None else None,
            message=str(raw.get("message") or raw.get("headline") or "ошибка сборки"),
            headline=str(raw.get("headline") or ""),
            exit_code=int(raw.get("exit_code") or 1),
            restored=bool(raw.get("restored")),
            details=tuple(raw.get("details") or ()),
        )
    except (KeyError, TypeError, ValueError):
        return None


def clear_last_build_failure(root: Path | None = None) -> None:
    data = _load_store(root)
    data["last_failure"] = None
    _save_store(root, data)


def record_build_failure(
    root: Path | None = None,
    *,
    exit_code: int,
    restored: bool,
    headline: str | None = None,
    details: list[str] | None = None,
) -> BuildFailureRecord:
    """Save structured report after failed Development Update."""
    parsed = parse_build_failure(root)
    use_headline = (headline or parsed.headline).strip()
    use_details = tuple(details or parsed.details)

    data = _load_store(root)
    build_number = int(data.get("next_build_number") or 1)
    record = BuildFailureRecord(
        build_number=build_number,
        timestamp=datetime.now(timezone.utc).isoformat(),
        file=parsed.file,
        line=parsed.line,
        message=parsed.message,
        headline=use_headline,
        exit_code=exit_code,
        restored=restored,
        details=use_details,
    )
    data["next_build_number"] = build_number + 1
    data["last_failure"] = asdict(record)
    data["last_failure"]["details"] = list(record.details)
    _save_store(root, data)

    from launcher.log_util import append_log

    append_log(f"Build #{build_number} failed — {record.file}:{record.line or '?'} — {record.message}")
    return record
