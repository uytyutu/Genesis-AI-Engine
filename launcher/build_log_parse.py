"""Parse frontend_build.log — actionable errors for CEO / developer."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from launcher.paths import log_dir

_TYPE_ERROR = re.compile(
    r"^\./(.+?):(\d+):(\d+)\s*\n?\s*Type error:\s*(.+)$",
    re.MULTILINE,
)
_TYPE_ERROR_INLINE = re.compile(
    r"^\./(.+?):(\d+):(\d+)\s*$",
)
_CANNOT_FIND_NAME = re.compile(r"Cannot find name '([^']+)'")
_MODULE_NOT_FOUND = re.compile(r"Module not found:\s*(.+)")
_FAILED_COMPILE = re.compile(r"Failed to compile\.?")
_BUILD_WORKER = re.compile(r"Next\.js build worker exited with code:\s*(\d+)")


@dataclass(frozen=True)
class ParsedBuildFailure:
    headline: str
    file: str
    line: int | None
    column: int | None
    message: str
    details: tuple[str, ...]


def _friendly_message(raw: str) -> str:
    text = raw.strip()
    m = _CANNOT_FIND_NAME.search(text)
    if m:
        return f"Import {m.group(1)} not found"
    if text.lower().startswith("module not found"):
        return text[:120]
    return text[:120]


def _read_log_tail(root=None, *, tail_chars: int = 4000) -> tuple[str, list[str]]:
    path = log_dir(root) / "frontend_build.log"
    if not path.is_file():
        return "", ["См. launcher/logs/frontend_build.log"]
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[-tail_chars:]
    except OSError:
        return "", []
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    return text, lines


def parse_build_failure(root=None, *, tail_chars: int = 4000) -> ParsedBuildFailure:
    """Structured fields for CEO report (file, line, short message)."""
    text, lines = _read_log_tail(root, tail_chars=tail_chars)
    if not text:
        return ParsedBuildFailure(
            headline="Сборка Mission Control не завершилась",
            file="—",
            line=None,
            column=None,
            message="npm run build завершился с ошибкой",
            details=tuple(lines),
        )

    details: list[str] = []
    file = "—"
    line_no: int | None = None
    col_no: int | None = None
    raw_msg = "npm run build завершился с ошибкой"

    m = _TYPE_ERROR.search(text)
    if m:
        rel, ln, col, msg = m.groups()
        file = rel.split("/")[-1]
        line_no = int(ln)
        col_no = int(col)
        raw_msg = msg.strip()
        headline = f"TypeScript: {rel}:{ln} — {raw_msg[:120]}"
        details.extend([f"./{rel}:{ln}", f"Type error: {raw_msg}"])
    else:
        headline = ""
        for pattern, label in (
            (_FAILED_COMPILE, "Next.js: ошибка компиляции"),
            (_BUILD_WORKER, "Сборка прервана (код {0})"),
            (_MODULE_NOT_FOUND, "Модуль не найден: {0}"),
            (re.compile(r"SyntaxError:\s*(.+)"), "Синтаксис: {0}"),
        ):
            for ln in reversed(lines):
                hit = pattern.search(ln)
                if hit:
                    headline = label.format(hit.group(1).strip()[:100]) if hit.lastindex else label
                    raw_msg = hit.group(1).strip()[:120] if hit.lastindex else headline
                    break
            if headline:
                break
        if not headline:
            for ln in reversed(lines):
                low = ln.lower()
                if "type error" in low or "error" in low or "failed" in low:
                    headline = ln.strip()[:140]
                    raw_msg = headline
                    break
        if not headline:
            headline = "npm run build завершился с ошибкой"

        for ln in reversed(lines):
            hit = _TYPE_ERROR_INLINE.search(ln)
            if hit:
                rel, ln_s, col_s = hit.groups()
                file = rel.split("/")[-1]
                line_no = int(ln_s)
                col_no = int(col_s)
                break

    capture = False
    for ln in lines[-80:]:
        if "Failed to compile" in ln:
            capture = True
            if not details:
                details.append(ln)
            continue
        if capture:
            if ln.startswith(">") or ln.startswith("npm "):
                break
            details.append(ln)
            if len(details) >= 12:
                break

    if not details:
        details = lines[-6:]

    return ParsedBuildFailure(
        headline=headline,
        file=file,
        line=line_no,
        column=col_no,
        message=_friendly_message(raw_msg),
        details=tuple(details),
    )


def extract_build_failure(root=None, *, tail_chars: int = 4000) -> tuple[str, list[str]]:
    """
    Return (headline, detail_lines) from launcher/logs/frontend_build.log.
    """
    parsed = parse_build_failure(root, tail_chars=tail_chars)
    return parsed.headline, list(parsed.details)
