"""Last failed Development Update report — persisted for CEO."""

from __future__ import annotations

from pathlib import Path

import pytest

from launcher.build_failure_report import (
    BuildFailureRecord,
    clear_last_build_failure,
    load_last_build_failure,
    record_build_failure,
)
from launcher.build_log_parse import parse_build_failure, _friendly_message


def test_friendly_message_cannot_find_name() -> None:
    assert _friendly_message("Cannot find name 'Badge'.") == "Import Badge not found"


def test_parse_build_failure_typescript(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    logs = tmp_path / "launcher" / "logs"
    logs.mkdir(parents=True)
    logs.joinpath("frontend_build.log").write_text(
        "Failed to compile.\n"
        "./app/components/GenesisConcierge.tsx:1286:12\n"
        "Type error: Cannot find name 'Badge'.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("launcher.build_log_parse.log_dir", lambda _=None: logs)
    parsed = parse_build_failure(tmp_path)
    assert parsed.file == "GenesisConcierge.tsx"
    assert parsed.line == 1286
    assert parsed.message == "Import Badge not found"
    assert "TypeScript" in parsed.headline


def test_record_and_load_increments_build_number(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    logs = tmp_path / "launcher" / "logs"
    logs.mkdir(parents=True)
    monkeypatch.setattr("launcher.build_failure_report.log_dir", lambda _=None: logs)
    monkeypatch.setattr("launcher.build_log_parse.log_dir", lambda _=None: logs)
    logs.joinpath("frontend_build.log").write_text(
        "./app/components/Foo.tsx:10:1\nType error: Cannot find name 'Bar'.\n",
        encoding="utf-8",
    )

    first = record_build_failure(tmp_path, exit_code=1, restored=True)
    assert first.build_number == 1
    assert first.file == "Foo.tsx"
    assert first.restored is True

    second = record_build_failure(tmp_path, exit_code=1, restored=False)
    assert second.build_number == 2

    loaded = load_last_build_failure(tmp_path)
    assert loaded is not None
    assert loaded.build_number == 2
    assert "Build #2" in loaded.display_text()
    assert "Bar" in loaded.message or "Import" in loaded.message


def test_clear_on_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    logs = tmp_path / "launcher" / "logs"
    logs.mkdir(parents=True)
    monkeypatch.setattr("launcher.build_failure_report.log_dir", lambda _=None: logs)
    monkeypatch.setattr("launcher.build_log_parse.log_dir", lambda _=None: logs)
    record_build_failure(tmp_path, exit_code=1, restored=False, headline="x", details=["y"])
    assert load_last_build_failure(tmp_path) is not None
    clear_last_build_failure(tmp_path)
    assert load_last_build_failure(tmp_path) is None


def test_record_short_summary() -> None:
    rec = BuildFailureRecord(
        build_number=128,
        timestamp="2026-07-11T12:00:00+00:00",
        file="GenesisConcierge.tsx",
        line=1286,
        message="Import Badge not found",
        headline="TypeScript error",
        exit_code=1,
        restored=True,
    )
    summary = rec.short_summary()
    assert "Build #128" in summary
    assert "GenesisConcierge.tsx" in summary
    assert "строка 1286" in summary
