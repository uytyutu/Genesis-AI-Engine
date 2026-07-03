"""Extract owner-facing errors from frontend/npm logs (filter Node internals)."""

from __future__ import annotations

import re
from pathlib import Path

from launcher.health import read_frontend_log_tail
from launcher.paths import log_dir

# Native stack / V8 noise — not actionable for the owner
_NOISE_PATTERNS = (
    re.compile(r"^.*node::", re.I),
    re.compile(r"^.*v8::", re.I),
    re.compile(r"^.*uv_", re.I),
    re.compile(r"RegExp::GetFlags", re.I),
    re.compile(r"ArrayBuffer::New", re.I),
    re.compile(r"node::Buffer::New", re.I),
    re.compile(r"^Native stack trace", re.I),
    re.compile(r"^FATAL ERROR:.*heap", re.I),
    re.compile(r"^<--- Last few GCs", re.I),
    re.compile(r"^----- Native stack", re.I),
    re.compile(r"^\s*\d+:\s+00007FF", re.I),
    re.compile(r"^\s*\d+:\s+000001", re.I),
    re.compile(r"^\[?\?25h", re.I),
    re.compile(r"^GET / \d+", re.I),
    re.compile(r"^GET /finance \d+", re.I),
    re.compile(r"^○ Compiling", re.I),
    re.compile(r"^✓ Compiled", re.I),
    re.compile(r"^⚠ Server is approaching", re.I),
)

# High-signal error lines (first match wins for headline)
_HEADLINE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"SyntaxError:\s*(.+)", re.I), "CSS/сборка: {0}"),
    (re.compile(r"ENOENT.*[\\/]\.next[\\/]", re.I), "Mission Control не собран — нужен npm run build (.next)"),
    (re.compile(r"Cannot find module.*[\\/]\.next[\\/]", re.I), "Сборка Mission Control повреждена — пересоберите .next"),
    (re.compile(r"Module not found:\s*(.+)", re.I), "Модуль не найден: {0}"),
    (re.compile(r"Cannot find module[:\s]+['\"]?(\.\/[^'\"]+)", re.I), "Модуль не найден: {0}"),
    (re.compile(r"TypeError:\s*(.+)", re.I), "TypeScript/JS: {0}"),
    (re.compile(r"ReferenceError:\s*(.+)", re.I), "Ошибка кода: {0}"),
    (re.compile(r"routes-manifest\.json", re.I), "Mission Control не собран — нужен npm run build"),
    (re.compile(r"Failed to compile", re.I), "Next.js: ошибка компиляции"),
    (re.compile(r"Build error", re.I), "Next.js: ошибка сборки"),
    (re.compile(r"EADDRINUSE|address already in use", re.I), "Порт 3000 уже занят"),
    (re.compile(r"npm ERR!", re.I), "Ошибка npm install"),
    (re.compile(r"error code (\w+)", re.I), "npm: код ошибки {0}"),
    (re.compile(r"JavaScript heap out of memory", re.I), "Node.js: нехватка памяти (часто из‑за ошибки сборки)"),
    (re.compile(r"\./app/globals\.css", re.I), "Ошибка в app/globals.css или tailwind.config.ts"),
    (re.compile(r"tailwind", re.I), "Ошибка Tailwind CSS"),
    (re.compile(r"postcss", re.I), "Ошибка PostCSS / Tailwind"),
    (re.compile(r"^⨯\s+(.+)", re.I), "{0}"),
)


def _read_log_lines(path: Path, *, max_lines: int = 200) -> list[str]:
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    lines = [ln.rstrip() for ln in text.splitlines()]
    return lines[-max_lines:] if len(lines) > max_lines else lines


def _is_noise(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    return any(p.search(stripped) for p in _NOISE_PATTERNS)


def _meaningful_lines(lines: list[str], *, limit: int = 50) -> list[str]:
    kept: list[str] = []
    for line in reversed(lines):
        if _is_noise(line):
            continue
        kept.append(line.strip())
        if len(kept) >= limit:
            break
    kept.reverse()
    return kept


def extract_frontend_error(root: Path | None = None) -> tuple[str, list[str]]:
    """Return (headline, meaningful_log_lines) from frontend.log + npm_install.log."""
    fe_lines = _read_log_lines(log_dir(root) / "frontend.log", max_lines=400)
    npm_lines = _read_log_lines(log_dir(root) / "npm_install.log", max_lines=100)
    combined = npm_lines + fe_lines

    headline = ""
    for pattern, template in _HEADLINE_PATTERNS:
        for line in reversed(combined):
            m = pattern.search(line)
            if m:
                headline = template.format(m.group(1).strip() if m.lastindex else "")
                if len(headline) > 120:
                    headline = headline[:117] + "…"
                break
        if headline:
            break

    if not headline:
        for line in reversed(combined):
            if _is_noise(line):
                continue
            low = line.lower()
            if "error" in low or "⨯" in line or "failed" in low:
                headline = line.strip()[:120]
                break

    if not headline:
        headline = "Frontend завершился — см. журнал ниже"

    meaningful = _meaningful_lines(combined, limit=50)
    if not meaningful and fe_lines:
        meaningful = _meaningful_lines(fe_lines, limit=20)

    return headline, meaningful


def format_owner_error(root: Path | None = None) -> str:
    headline, lines = extract_frontend_error(root)
    parts = ["Frontend завершился.", "", f"Причина:\n{headline}"]
    if lines:
        parts.append("")
        parts.append("--- frontend.log (последние строки) ---")
        parts.extend(lines[-25:])
    return "\n".join(parts)


def frontend_log_path(root: Path | None = None) -> Path:
    return log_dir(root) / "frontend.log"
