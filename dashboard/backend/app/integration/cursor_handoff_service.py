"""R0.5 — Cursor handoff: task queue, semi-auto open, verify gate. Full API bridge = R8."""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.factory.factory_service import FactoryService
from app.integration.cursor_adapter import open_workspace
from app.integration.finance_service import FinanceService
from app.integration.system_check_service import SystemCheckService

_TASK_STEPS = (
    ("analyze", "Анализ задачи и сбор контекста"),
    ("dispatch", "Промпт готов · передача в Cursor"),
    ("awaiting_cursor", "Ожидание работы Cursor (вставьте промпт — Ctrl+V)"),
    ("verify", "Проверка (pytest + система)"),
    ("ready", "Готово к проверке владельцем"),
)


def _find_genesis_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / "PROJECT_STATE.md").exists() and (candidate / "dashboard").exists():
            return candidate
    return None


def _tail_text(path: Path, chars: int = 3500) -> str:
    if not path.is_file():
        return ""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return raw[-chars:].strip()


def _excerpt_md(path: Path, max_lines: int = 35) -> str:
    if not path.is_file():
        return ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[:max_lines]).strip()


def _progress_for_state(state: str) -> int | None:
    """Percent only for phases with real work (verify / outcome). Semi-auto steps use labels."""
    return {
        "verifying": 85,
        "ready": 100,
        "failed": 100,
    }.get(state)


def _progress_label(state: str) -> str:
    return {
        "queued": "В очереди",
        "prompt_ready": "Промпт сформирован",
        "clipboard_ready": "Промпт в буфере — откройте Cursor",
        "cursor_opened": "Cursor открыт — вставьте промпт (Ctrl+V)",
        "awaiting_cursor": "Ожидание работы в Cursor (ваш шаг)",
        "verifying": "Проверка: pytest + System Check",
        "ready": "✔ Выполнено — готово к проверке владельцем",
        "failed": "✘ Ошибка — проверка не пройдена",
    }.get(state, "В работе")


def _steps_payload(state: str) -> list[dict]:
    order = [s[0] for s in _TASK_STEPS]
    idx = order.index(state) if state in order else 0
    if state == "failed":
        idx = order.index("verify")
    rows = []
    for i, (sid, label) in enumerate(_TASK_STEPS):
        if state == "ready":
            done = True
            active = sid == "ready"
        elif state == "failed":
            done = i < idx
            active = sid == "verify"
        else:
            done = i < idx
            active = sid == state or (state == "cursor_opened" and sid == "dispatch")
        rows.append({"id": sid, "label": label, "done": done, "active": active})
    return rows


class CursorHandoffService:
    """Task queue + verify. Cursor has no public auto-task API — semi-auto until R8."""

    MODE = "semi_auto"

    def __init__(
        self,
        memory_dir: Path,
        system_check: SystemCheckService,
        factory: FactoryService,
        finance: FinanceService,
    ) -> None:
        self._memory = memory_dir
        self._system_check = system_check
        self._factory = factory
        self._finance = finance
        self._memory.mkdir(parents=True, exist_ok=True)
        self._root = _find_genesis_root(Path(__file__).resolve())

    def _tasks_path(self) -> Path:
        return self._memory / "cursor_tasks.json"

    def _load_tasks(self) -> list[dict]:
        path = self._tasks_path()
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save_tasks(self, tasks: list[dict]) -> None:
        self._tasks_path().write_text(
            json.dumps(tasks[-30:], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _upsert_task(self, task: dict) -> None:
        tasks = self._load_tasks()
        tasks = [t for t in tasks if t.get("task_id") != task.get("task_id")]
        tasks.append(task)
        self._save_tasks(tasks)

    def active_task(self) -> dict | None:
        tasks = self._load_tasks()
        for task in reversed(tasks):
            if task.get("state") not in ("ready", "failed"):
                return self._enrich_task(task)
        if tasks:
            return self._enrich_task(tasks[-1])
        return None

    def get_task(self, task_id: str) -> dict | None:
        for task in self._load_tasks():
            if task.get("task_id") == task_id:
                return self._enrich_task(task)
        return None

    def _enrich_task(self, task: dict) -> dict:
        state = task.get("state", "queued")
        pct = _progress_for_state(state)
        return {
            **task,
            "progress_percent": pct,
            "progress_label": _progress_label(state),
            "progress_is_estimated": pct is None,
            "steps": _steps_payload(state),
        }

    def list_tasks(self, limit: int = 15) -> list[dict]:
        tasks = self._load_tasks()
        enriched = [self._enrich_task(t) for t in tasks[-limit:]]
        return list(reversed(enriched))

    def handoff_history(self, limit: int = 20) -> list[dict]:
        journal = self._memory / "cursor_handoffs.jsonl"
        if not journal.is_file():
            return []
        try:
            lines = journal.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        rows: list[dict] = []
        for line in reversed(lines[-limit:]):
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            rows.append(
                {
                    "at": row.get("at"),
                    "kind": row.get("kind"),
                    "task_note": row.get("task_note"),
                    "chars": row.get("chars"),
                }
            )
        return rows

    def _owner_context_block(self) -> str:
        parts: list[str] = []
        config_path = self._memory / "launcher_config.json"
        if config_path.is_file():
            try:
                cfg = json.loads(config_path.read_text(encoding="utf-8"))
                owner = cfg.get("owner_name") or cfg.get("owner")
                company = cfg.get("company_name")
                if owner or company:
                    parts.append(
                        f"Владелец: {owner or '—'} · Компания: {company or 'Genesis Company'}"
                    )
            except (json.JSONDecodeError, OSError):
                pass

        milestones_path = self._memory / "owner_milestones.json"
        if milestones_path.is_file():
            try:
                ms = json.loads(milestones_path.read_text(encoding="utf-8"))
                approved = ms.get("owner_approved_changes") or ms.get("approved") or []
                if isinstance(approved, list) and approved:
                    parts.append("Утверждённые владельцем изменения:")
                    for item in approved[-5:]:
                        if isinstance(item, str):
                            parts.append(f"- {item}")
                        elif isinstance(item, dict):
                            parts.append(f"- {item.get('label', item)}")
            except (json.JSONDecodeError, OSError):
                pass

        tasks = self._load_tasks()
        active_notes = [
            t.get("task_note")
            for t in tasks[-5:]
            if t.get("task_note") and t.get("state") not in ("ready", "failed")
        ]
        if active_notes:
            parts.append("Активные задачи Cursor:")
            parts.extend(f"- {n}" for n in active_notes if n)

        last = tasks[-1] if tasks else None
        if last and last.get("state") in ("ready", "failed"):
            parts.append(
                f"Последняя задача: {last.get('state_label', last.get('state'))}"
            )

        return "\n".join(parts) if parts else "(контекст владельца — см. PROJECT_STATE и Factory)"

    def status(self) -> dict:
        active = self.active_task()
        cursor_cli = bool(self._cursor_cli_available())
        if active and active.get("state") not in ("ready", "failed"):
            return {
                "mode": self.MODE,
                "bridge_ready": False,
                "label": "Задача в работе — см. прогресс ниже",
                "status_icon": "🟡",
                "status_label": active.get("state_label", "Выполняется"),
                "hint": (
                    "Полная автоматизация без Ctrl+V — R8 (Cursor Bridge API). "
                    "Сейчас: промпт + открытие проекта в Cursor."
                ),
                "cursor_cli_available": cursor_cli,
                "active_task_id": active.get("task_id"),
            }
        return {
            "mode": self.MODE,
            "bridge_ready": False,
            "label": "Полуавто — промпт + открытие Cursor",
            "status_icon": "🟢",
            "status_label": "Готов к задаче",
            "hint": (
                "Нажмите «Отправить задачу» — Genesis скопирует промпт и откроет Cursor. "
                "Вставьте в чат (Ctrl+V). Затем «Проверить результат»."
            ),
            "cursor_cli_available": cursor_cli,
            "active_task_id": active.get("task_id") if active else None,
        }

    def _cursor_cli_available(self) -> bool:
        from app.integration.cursor_adapter import find_cursor_cli

        return find_cursor_cli() is not None

    def _log_excerpts(self) -> str:
        if not self._root:
            return "(корень проекта не найден)"
        log_dir = self._root / "launcher" / "logs"
        parts: list[str] = []
        for name in ("backend.log", "frontend.log"):
            tail = _tail_text(log_dir / name)
            if tail:
                parts.append(f"### {name} (хвост)\n```\n{tail}\n```")
        return "\n\n".join(parts) if parts else "(логи пусты или недоступны)"

    def _roadmap_excerpt(self) -> str:
        if not self._root:
            return ""
        path = self._root / "Docs" / "ROADMAP.md"
        if not path.is_file():
            path = self._root / "docs" / "ROADMAP.md"
        return _excerpt_md(path, 45)

    def _project_state_excerpt(self) -> str:
        if not self._root:
            return ""
        return _excerpt_md(self._root / "PROJECT_STATE.md", 30)

    def _products_summary(self) -> str:
        products = self._factory.list_products()
        if not products:
            return "Продуктов Factory пока нет."
        lines = []
        for p in products[:5]:
            lines.append(
                f"- {p.get('business_name', p.get('product_id'))}: "
                f"quality {p.get('quality_percent')}% · "
                f"approved={p.get('owner_approved')} · published={p.get('published')}"
            )
        return "\n".join(lines)

    def _system_summary(self) -> str:
        check = self._system_check.run()
        tech = [f"{r['icon']} {r['label']}: {r['message']}" for r in check["technical_checks"][:8]]
        warn = check.get("warnings") or []
        lines = [f"Готовность: {check['headline']}", *tech]
        if warn:
            lines.append("Предупреждения: " + "; ".join(warn[:5]))
        return "\n".join(lines)

    def build_prompt(self, kind: str = "task", task_note: str | None = None) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        fin = self._finance.revenue_summary()
        demo = self._finance.is_demo_mode()

        header = {
            "task": "Задача для Cursor (Genesis → инженер за кулисами)",
            "status": "Статус Genesis для Cursor — без новых модулей, только контекст",
            "verify": "Проверка результата после работы Cursor",
            "apply": "Чеклист перед применением изменений владельцем",
        }.get(kind, "Задача для Cursor")

        owner_ctx = self._owner_context_block()

        sections = [
            f"# {header}",
            f"Сформировано Genesis: {now}",
            f"Режим: R0.5 semi-auto (полный Bridge = R8)",
            "",
            "## Контекст владельца (память Genesis)",
            owner_ctx,
            "",
            "## Текущий этап",
            self._project_state_excerpt() or "(PROJECT_STATE.md недоступен)",
            "",
            "## Roadmap (начало)",
            self._roadmap_excerpt() or "(ROADMAP недоступен)",
            "",
            "## Состояние системы",
            self._system_summary(),
            "",
            "## Финансы (честные данные)",
            f"Демо: {demo} · Доход сегодня: {fin.get('revenue_today_eur', 0)} € · "
            f"За месяц: {fin.get('revenue_month_eur', 0)} €",
            "",
            "## Factory",
            self._products_summary(),
        ]

        if kind == "task":
            sections.extend(
                [
                    "",
                    "## Задача владельца",
                    (task_note or "Продолжить работу по Roadmap — приоритет R1.").strip(),
                    "",
                    "## Правила",
                    "- Vision Freeze: только R1-цикл до первого клиента.",
                    "- Genesis предлагает → Cursor делает → Genesis проверяет → владелец ✔.",
                ]
            )
        elif kind == "verify":
            sections.extend(
                [
                    "",
                    "## Проверить после изменений Cursor",
                    "1. `py -m pytest tests/ -q`",
                    "2. Mission Control открывается",
                    "",
                    "## Логи",
                    self._log_excerpts(),
                ]
            )
        elif kind == "status":
            sections.extend(["", "## Логи", self._log_excerpts()])
        elif kind == "apply":
            sections.extend(
                [
                    "",
                    "## Перед «Применить» (владелец)",
                    "- Прочитать diff",
                    "- Тесты зелёные",
                    "- ✔ владельца перед production",
                ]
            )

        if kind in ("task", "status", "verify"):
            sections.extend(["", "## Логи", self._log_excerpts()])

        prompt = "\n".join(sections).strip()
        record = {
            "at": now,
            "kind": kind,
            "task_note": task_note,
            "chars": len(prompt),
            "prompt": prompt,
        }
        self._save_handoff(record)
        return {
            "ok": True,
            "kind": kind,
            "prompt": prompt,
            "chars": len(prompt),
            "copied_hint": "Вставьте в чат Cursor (Ctrl+V).",
            **self.status(),
        }

    def submit_task(
        self,
        task_note: str | None = None,
        *,
        auto_open: bool = True,
    ) -> dict:
        """Build prompt, queue task, optionally open Cursor on Genesis repo."""
        built = self.build_prompt("task", task_note)
        now = datetime.now(timezone.utc).isoformat()
        task_id = f"ct-{uuid.uuid4().hex[:12]}"
        task: dict = {
            "task_id": task_id,
            "created_at": now,
            "updated_at": now,
            "task_note": task_note,
            "prompt_chars": built["chars"],
            "state": "prompt_ready",
            "state_label": "Промпт готов",
            "cursor_opened": False,
            "cursor_message": None,
            "verify_summary": None,
        }

        if auto_open and self._root:
            ok, msg = open_workspace(self._root)
            task["cursor_opened"] = ok
            task["cursor_message"] = msg
            task["state"] = "cursor_opened" if ok else "clipboard_ready"
            task["state_label"] = "Cursor открыт — вставьте промпт" if ok else "Вставьте промпт в Cursor"
        else:
            task["state"] = "clipboard_ready"
            task["state_label"] = "Промпт в буфере — откройте Cursor"

        task["state"] = "awaiting_cursor"
        task["state_label"] = "Ожидание работы в Cursor"
        task["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._upsert_task(task)

        return {
            **built,
            "task": self._enrich_task(task),
            "copied_hint": (
                "Промпт скопирован. Cursor открыт — вставьте в чат (Ctrl+V). "
                "После правок нажмите «Проверить результат»."
                if task.get("cursor_opened")
                else "Промпт скопирован. Откройте Cursor и вставьте (Ctrl+V)."
            ),
        }

    def verify_task(self, task_id: str | None = None) -> dict:
        """Run pytest + system check — honest verify gate."""
        task = self.get_task(task_id) if task_id else self.active_task()
        if not task:
            return {"ok": False, "message": "Нет активной задачи Cursor."}

        task_id = task["task_id"]
        task["state"] = "verifying"
        task["state_label"] = "Проверка…"
        task["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._upsert_task(task)

        pytest_ok = False
        pytest_tail = ""
        if self._root:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
                    cwd=self._root,
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                pytest_tail = (result.stdout or "") + (result.stderr or "")
                pytest_ok = result.returncode == 0
            except (OSError, subprocess.TimeoutExpired) as exc:
                pytest_tail = str(exc)

        sys_check = self._system_check.run()
        system_ok = bool(sys_check.get("ready"))

        ok = pytest_ok and system_ok
        summary_lines = [
            f"pytest: {'✔' if pytest_ok else '✘'}",
            f"System Check: {'✔' if system_ok else '✘'} — {sys_check.get('headline', '')}",
        ]
        if not pytest_ok and pytest_tail.strip():
            summary_lines.append("")
            summary_lines.append(pytest_tail.strip()[-800:])

        task["state"] = "ready" if ok else "failed"
        task["state_label"] = "Готово к проверке владельцем" if ok else "Проверка не пройдена"
        task["verify_summary"] = "\n".join(summary_lines)
        task["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._upsert_task(task)

        return {
            "ok": ok,
            "task": self._enrich_task(task),
            "verify_summary": task["verify_summary"],
            "message": task["state_label"],
        }

    def last_handoff(self) -> dict | None:
        path = self._memory / "cursor_last_handoff.json"
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _save_handoff(self, record: dict) -> None:
        last = self._memory / "cursor_last_handoff.json"
        last.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        journal = self._memory / "cursor_handoffs.jsonl"
        with open(journal, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
