from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from app.integration.health_service import HealthService
from app.integration.task_service import TaskService

if TYPE_CHECKING:
    from app.integration.finance_service import FinanceService

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_TIPS = [
    "Добро пожаловать в вашу цифровую компанию.",
    "Нажмите «Создать продукт» — начните новый проект.",
    "Все задачи видны в разделе «Проекты».",
    "Genesis работает локально — ваши данные остаются на компьютере.",
]


class OwnerDashboardService:
    def __init__(
        self,
        tasks: TaskService,
        health: HealthService,
        memory_dir: Path | None = None,
        started_at: datetime | None = None,
        finance: FinanceService | None = None,
    ) -> None:
        self._tasks = tasks
        self._health = health
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._started_at = started_at or datetime.now(timezone.utc)
        self._finance = finance

    def _load_config(self) -> dict:
        config_path = self._memory / "launcher_config.json"
        if config_path.exists():
            try:
                return json.loads(config_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def owner_name(self) -> str:
        name = str(self._load_config().get("owner_name", "")).strip()
        return name or "Владелец"

    def _last_launch_label(self) -> str:
        raw = str(self._load_config().get("last_launch_at", "")).strip()
        if not raw:
            return "ещё не записан"
        try:
            launched = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if launched.tzinfo is None:
                launched = launched.replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - launched
            minutes = int(delta.total_seconds() // 60)
            if minutes < 1:
                return "только что"
            if minutes < 60:
                return f"{minutes} мин. назад"
            hours = minutes // 60
            if hours < 24:
                return f"{hours} ч. назад"
            days = hours // 24
            return f"{days} дн. назад"
        except ValueError:
            return raw

    def dashboard(self) -> dict:
        stats = self._tasks.stats_today()
        health = self._health.check_all()
        queue = self._tasks.queue_stats()
        config = self._load_config()
        core_ok = all(
            health.get(k) in ("online", "degraded") for k in ("kernel", "brain", "queue", "audit")
        )
        running = health.get("kernel") == "online" and health.get("brain") in (
            "online",
            "degraded",
        )
        uptime = datetime.now(timezone.utc) - self._started_at
        hours, rem = divmod(int(uptime.total_seconds()), 3600)
        minutes, _ = divmod(rem, 60)
        tip_index = datetime.now().timetuple().tm_yday % len(_TIPS)
        name = self.owner_name()
        pending = queue.pending + queue.running
        load = min(100, pending * 8 + (10 if queue.running else 0))
        revenue = (
            self._finance.revenue_summary()
            if self._finance
            else {"revenue_today_eur": 0.0, "revenue_month_eur": 0.0}
        )

        services = []
        for key, label in (
            ("kernel", "Kernel"),
            ("brain", "Brain"),
            ("queue", "Очередь"),
            ("audit", "Журнал"),
        ):
            ok = health.get(key) in ("online", "degraded")
            services.append(f"{'✔' if ok else '✘'} {label} работает" if ok else f"✘ {label} не отвечает")

        return {
            "owner_name": name,
            "greeting": self._greeting(name),
            "system_running": running,
            "all_services_ok": core_ok and running,
            "tasks_completed_today": stats["completed_today"],
            "errors_today": stats["failed_today"],
            "uptime_label": f"{hours} ч {minutes} мин",
            "last_launch_label": self._last_launch_label(),
            "daily_goal": str(config.get("daily_goal", "Создать первый цифровой продукт.")),
            "queue_completed": queue.completed,
            "queue_failed": queue.failed,
            "queue_pending": queue.pending,
            "products_count": self._products_count(),
            "products_created_today": self._products_created_today(),
            "revenue_today_eur": revenue["revenue_today_eur"],
            "revenue_month_eur": revenue["revenue_month_eur"],
            "system_load_percent": load,
            "recent_events": self._recent_events(),
            "tip": _TIPS[tip_index],
            "services_summary": services,
        }

    def _greeting(self, name: str) -> str:
        hour = datetime.now().hour
        if hour < 12:
            return f"Доброе утро, {name}"
        if hour < 18:
            return f"Добрый день, {name}"
        return f"Добрый вечер, {name}"

    def _recent_events(self) -> list[dict[str, str]]:
        events = []
        for item in self._tasks.recent_activity(limit=6):
            icon = "✔" if "complet" in item.message.lower() else "•"
            events.append({"icon": icon, "message": item.message})
        if not events:
            events.append({"icon": "💡", "message": "Нажмите «Создать продукт» — начните первый проект"})
        return events

    def _products_created_today(self) -> int:
        path = self._memory / "factory_intents.jsonl"
        if not path.exists():
            return 0
        today = datetime.now(timezone.utc).date().isoformat()
        count = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if str(row.get("at", "")).startswith(today):
                    count += 1
            except json.JSONDecodeError:
                continue
        return count

    def _products_count(self) -> int:
        sandbox = self._memory.parent / "sandbox"
        if not sandbox.exists():
            return 0
        return sum(1 for p in sandbox.iterdir() if p.is_dir())
