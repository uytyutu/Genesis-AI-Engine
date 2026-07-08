"""System Check — technical + business health before Virtus Core works."""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from app.integration.finance_service import FinanceService
from app.integration.genesis_brain.public_brand import BRAND_NAME
from app.integration.health_service import HealthService
from app.integration.module_status_service import ModuleStatusService
from app.integration.owner_dashboard_service import OwnerDashboardService
from app.integration.task_service import TaskService

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"
_INTERNET_CACHE_TTL_SEC = 300.0
_internet_cache: tuple[float, bool] | None = None

_OWNER_LABELS = {
    "backend": "Backend",
    "frontend": "Frontend",
    "api": "API",
    "kernel": "Kernel",
    "brain": "Brain",
    "queue": "Очередь задач",
    "audit": "Журнал",
    "factory": "Factory",
    "launcher": "Launcher",
    "payment_hub": "Payment Hub",
    "internet": "Интернет",
    "ai_models": "AI Models",
    "storage": "Хранилище",
    "backup": "Backup",
    "license": "Лицензия",
    "security": "Безопасность",
}


class SystemCheckService:
    def __init__(
        self,
        health: HealthService,
        modules: ModuleStatusService,
        tasks: TaskService,
        owner: OwnerDashboardService,
        finance: FinanceService,
        memory_dir: Path | None = None,
    ) -> None:
        self._health = health
        self._modules = modules
        self._tasks = tasks
        self._owner = owner
        self._finance = finance
        self._memory = memory_dir or _DEFAULT_MEMORY

    def _status_row(
        self,
        check_id: str,
        ok: bool | None,
        warning: str | None = None,
        detail: str | None = None,
    ) -> dict:
        if ok is True:
            icon = "✔"
            state = "ok"
        elif ok is False:
            icon = "✘"
            state = "error"
        else:
            icon = "⚠"
            state = "warning"
        return {
            "id": check_id,
            "label": _OWNER_LABELS.get(check_id, check_id),
            "icon": icon,
            "state": state,
            "message": warning or detail or ("Работает" if ok else "Не готово"),
        }

    def _probe_url(self, url: str, timeout: float = 2.5) -> bool:
        try:
            with urlopen(url, timeout=timeout) as response:
                return response.status < 500
        except (URLError, OSError, TimeoutError):
            return False

    def _probe_internet(self) -> bool:
        global _internet_cache
        now = time.monotonic()
        if _internet_cache is not None and now - _internet_cache[0] < _INTERNET_CACHE_TTL_SEC:
            return _internet_cache[1]
        ok = False
        try:
            with urlopen("https://www.python.org", timeout=2.0) as response:
                ok = response.status < 500
        except (URLError, OSError, TimeoutError):
            ok = False
        _internet_cache = (now, ok)
        return ok

    def _storage_ok(self) -> bool:
        try:
            self._memory.mkdir(parents=True, exist_ok=True)
            probe = self._memory / ".storage_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return True
        except OSError:
            return False

    def _factory_ready(self) -> bool | None:
        if self._probe_url("http://127.0.0.1:8000/api/factory/products", timeout=1.5):
            return True
        module_map = {m["id"]: m["status"] for m in self._modules.list_modules()}
        if module_map.get("factory") == "online":
            return True
        return None

    def run(self) -> dict:
        live = self._health.check_all()
        dash = self._owner.dashboard()
        fin_cfg = self._finance._load_config()
        queue = self._tasks.queue_stats()
        demo = self._finance.is_demo_mode()
        factory_ready = self._factory_ready()

        technical = [
            self._status_row(
                "backend",
                True,
                detail="Порт 8000 (in-process)",
            ),
            self._status_row(
                "frontend",
                self._probe_url("http://127.0.0.1:3000", timeout=2.0),
                detail="Mission Control :3000",
            ),
            self._status_row(
                "api",
                True,
                detail="REST API (in-process)",
            ),
            self._status_row("kernel", live.get("kernel") == "online"),
            self._status_row(
                "brain",
                live.get("brain") in ("online", "degraded"),
                warning="Brain на паузе" if live.get("brain") == "degraded" else None,
            ),
            self._status_row(
                "factory",
                factory_ready is True,
                warning=f"Factory недоступен — перезапустите {BRAND_NAME}"
                if factory_ready is not True
                else None,
                detail="Landing Page · create · improve · preview",
            ),
            self._status_row("launcher", dash["system_running"], detail="Launcher + серверы"),
            self._status_row(
                "payment_hub",
                bool(fin_cfg.get("payment_provider")),
                warning="Не подключён Payment Hub. Доход временно недоступен."
                if not fin_cfg.get("payment_provider") and not demo
                else None,
            ),
            self._status_row("internet", self._probe_internet()),
            self._status_row(
                "ai_models",
                None,
                warning="Внешние модели подключаются по мере готовности отделов",
            ),
            self._status_row("storage", self._storage_ok()),
            self._status_row(
                "backup",
                None,
                warning="Резервное копирование — следующий этап",
            ),
            self._status_row("license", True, detail="Локальная установка"),
            self._status_row("security", True, detail="Guardian — в разработке"),
        ]

        products = dash["products_count"]
        intents_path = self._memory / "factory_intents.jsonl"
        has_intents = intents_path.exists() and bool(intents_path.read_text(encoding="utf-8").strip())
        load_ok = queue.pending < 50
        errors_ok = dash["errors_today"] == 0
        budget_ok = fin_cfg.get("payment_provider") or dash["errors_today"] == 0

        business = [
            self._status_row(
                "published_products",
                True if products > 0 else None,
                warning="Нет опубликованных продуктов — начните с «Создать продукт»"
                if products == 0
                else None,
                detail=f"Продуктов: {products}" if products else None,
            ),
            self._status_row(
                "active_templates",
                True if has_intents else None,
                warning="Нет активных шаблонов — создайте первый запрос в Factory"
                if not has_intents
                else None,
            ),
            self._status_row(
                "capacity",
                load_ok,
                warning="Высокая загрузка очереди" if not load_ok else None,
                detail=f"В очереди: {queue.pending}",
            ),
            self._status_row(
                "budget",
                budget_ok,
                warning="Контроль расходов — после подключения Payment Hub"
                if not fin_cfg.get("payment_provider")
                else None,
            ),
            self._status_row(
                "critical_errors",
                errors_ok,
                warning=f"Критических ошибок сегодня: {dash['errors_today']}" if not errors_ok else None,
            ),
        ]

        for row in business:
            row["label"] = {
                "published_products": "Опубликованные продукты",
                "active_templates": "Активные шаблоны",
                "capacity": "Свободные мощности",
                "budget": "Расходы в бюджете",
                "critical_errors": "Критические ошибки",
            }.get(row["id"], row["label"])

        core_ok = all(
            r["state"] == "ok"
            for r in technical
            if r["id"] in ("backend", "frontend", "api", "kernel", "brain", "storage")
        )
        has_blocking = any(r["state"] == "error" for r in technical)
        ready = core_ok and not has_blocking and errors_ok

        warnings = [r["message"] for r in technical + business if r["state"] in ("warning", "error")]

        return {
            "ready": ready,
            "headline": "Система готова к работе." if ready else "Требуется внимание владельца.",
            "technical_checks": technical,
            "business_checks": business,
            "warnings": warnings[:6],
            "demo_mode": demo,
        }
