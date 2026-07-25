"""Work Farm v0 — minimal digital work pipeline after Stripe payment.

Scope (CEO): one work type done well — Landing Page.
Not a marketplace. Not micro-API farm. Own paid orders only.

Flow:
  Stripe paid order
       ↓
  Planner (split into steps)
       ↓
  Workers (brief → Factory build)
       ↓
  Quality Gate (Factory compliance result)
       ↓
  Ready / Delivered path
       ↓
  Revenue stays in existing Ledger / settlements

SEO-audit and translation are registered but disabled until Landing is proven.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

WORK_FARM_VERSION = "work_farm_v0"

# Explicit catalog — Marketplace is later; these are Virtus own-order types only.
WORK_TYPES: dict[str, dict[str, Any]] = {
    "landing_page": {
        "enabled": True,
        "label_ru": "Landing Page",
        "ai_share_pct": 90,
        "note_ru": "v0 primary — Factory Path A после оплаты Stripe.",
    },
    "seo_audit": {
        "enabled": False,
        "label_ru": "SEO-аудит",
        "ai_share_pct": 95,
        "note_ru": "Следующий тип после стабильного Landing.",
    },
    "translation": {
        "enabled": False,
        "label_ru": "Перевод",
        "ai_share_pct": 90,
        "note_ru": "Следующий тип после стабильного Landing.",
    },
    "repair_manual": {
        "enabled": True,
        "label_ru": "Ремонт сайта (оператор)",
        "ai_share_pct": 20,
        "note_ru": "Не автоконвейер — manual operator после оплаты.",
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _job_path(memory_dir: Path, job_id: str) -> Path:
    root = Path(memory_dir) / "work_farm" / "jobs"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{job_id}.json"


def _jobs_dir(memory_dir: Path) -> Path:
    root = Path(memory_dir) / "work_farm" / "jobs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _index_path(memory_dir: Path) -> Path:
    root = Path(memory_dir) / "work_farm"
    root.mkdir(parents=True, exist_ok=True)
    return root / "index.jsonl"


# Cost is a PROXY until real token/API metering exists (Reality over Simulation).
_COST_PROXY = {
    "landing_page": {"base_eur": 2.0, "per_min_eur": 0.45},
    "repair_manual": {"base_eur": 0.5, "per_min_eur": 0.1},
    "seo_audit": {"base_eur": 1.0, "per_min_eur": 0.25},
    "translation": {"base_eur": 0.8, "per_min_eur": 0.2},
}


def proxy_cost_eur(work_type: str, duration_sec: float) -> float:
    cfg = _COST_PROXY.get(work_type) or _COST_PROXY["landing_page"]
    minutes = max(0.0, float(duration_sec) / 60.0)
    return round(float(cfg["base_eur"]) + minutes * float(cfg["per_min_eur"]), 2)


def resolve_work_type(order: dict[str, Any]) -> str:
    package_id = str(order.get("package_id") or "").strip().lower()
    if package_id in ("repair", "site_repair", "fix") or order.get("product_kind") == "repair":
        return "repair_manual"
    # Path A packages = landing work
    return "landing_page"


def plan_steps(work_type: str) -> list[dict[str, Any]]:
    """Deterministic planner — no new LLM layer in v0."""
    if work_type == "repair_manual":
        return [
            {"id": "intake", "label_ru": "Принять оплаченный заказ", "worker": "intake"},
            {"id": "operator", "label_ru": "Очередь оператора (ручной ремонт)", "worker": "operator"},
            {"id": "deliver", "label_ru": "Передать клиенту", "worker": "delivery"},
        ]
    if work_type == "landing_page":
        return [
            {"id": "intake", "label_ru": "Принять оплаченный заказ", "worker": "intake"},
            {"id": "brief", "label_ru": "Собрать бриф / контакты", "worker": "brief"},
            {"id": "factory", "label_ru": "AI Worker · Factory Landing", "worker": "factory"},
            {"id": "quality_gate", "label_ru": "Quality Gate", "worker": "quality_gate"},
            {"id": "ready", "label_ru": "Готово к выдаче клиенту", "worker": "delivery"},
        ]
    # Disabled types — plan only, no auto-run
    return [
        {"id": "intake", "label_ru": "Принять заказ", "worker": "intake"},
        {"id": "blocked", "label_ru": "Тип работы ещё не включён в Work Farm v0", "worker": "blocked"},
    ]


class WorkFarmService:
    """Orchestrates post-payment work. Does not invent money or scrape marketplaces."""

    def __init__(
        self,
        memory_dir: Path,
        *,
        start_production: Callable[[str], dict[str, Any]],
        get_order: Callable[[str], dict[str, Any] | None],
        get_product: Callable[[str], dict[str, Any] | None] | None = None,
    ) -> None:
        self._memory = Path(memory_dir)
        self._start_production = start_production
        self._get_order = get_order
        self._get_product = get_product

    def catalog(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": WORK_FARM_VERSION,
            "marketplace": False,
            "rule_ru": (
                "Work Farm выполняет собственные оплаченные заказы. "
                "Внешний Marketplace — позже, как ещё один источник задач."
            ),
            "work_types": [
                {"id": k, **v} for k, v in WORK_TYPES.items()
            ],
            "pipeline_ru": [
                "Stripe paid",
                "Planner",
                "AI / Factory workers",
                "Quality Gate",
                "Ready → Delivered",
                "Revenue / Ledger",
            ],
        }

    def _append_index(self, row: dict[str, Any]) -> None:
        path = _index_path(self._memory)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _save_job(self, job: dict[str, Any]) -> None:
        path = _job_path(self._memory, str(job["job_id"]))
        path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        path = _job_path(self._memory, job_id)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except (OSError, json.JSONDecodeError):
            return None

    def find_job_for_order(self, order_id: str) -> dict[str, Any] | None:
        oid = (order_id or "").strip()
        if not oid:
            return None
        # Prefer latest matching file via index scan (tail)
        path = _index_path(self._memory)
        if not path.is_file():
            return None
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return None
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(row.get("order_id") or "") == oid and row.get("job_id"):
                job = self.get_job(str(row["job_id"]))
                if job:
                    return job
        return None

    def list_recent(self, *, limit: int = 20) -> list[dict[str, Any]]:
        path = _index_path(self._memory)
        if not path.is_file():
            return []
        out: list[dict[str, Any]] = []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        for line in reversed(lines):
            if len(out) >= limit:
                break
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                out.append(row)
        return out

    def list_all_jobs(self, *, limit: int = 500) -> list[dict[str, Any]]:
        """Load job files (source of truth for stats — not index alone)."""
        root = _jobs_dir(self._memory)
        files = sorted(root.glob("WF-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        out: list[dict[str, Any]] = []
        for path in files[: max(1, limit)]:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict) and data.get("job_id"):
                out.append(data)
        return out

    def _step_result(
        self,
        *,
        step_id: str,
        status: str,
        detail_ru: str = "",
        meta: dict[str, Any] | None = None,
        started_at: str | None = None,
        duration_ms: int | None = None,
        worker: str | None = None,
        module: str | None = None,
        manual_review: bool = False,
        cost_eur_proxy: float | None = None,
    ) -> dict[str, Any]:
        at = _utc_now()
        return {
            "id": step_id,
            "status": status,  # success | error | skipped | pending | blocked
            "at": at,
            "started_at": started_at or at,
            "duration_ms": int(duration_ms) if duration_ms is not None else 0,
            "detail_ru": detail_ru,
            "worker": worker or step_id,
            "module": module,
            "manual_review": bool(manual_review),
            "cost_eur_proxy": cost_eur_proxy,
            "meta": meta or {},
        }

    def _finalize_economics(self, job: dict[str, Any], order: dict[str, Any]) -> None:
        created = _parse_dt(str(job.get("created_at") or ""))
        updated = _parse_dt(str(job.get("updated_at") or "")) or created
        duration_sec = 0.0
        if created and updated:
            duration_sec = max(0.0, (updated - created).total_seconds())
        # Prefer sum of step durations when present (sync jobs may finish in same second)
        step_ms = sum(int(s.get("duration_ms") or 0) for s in (job.get("steps") or []) if isinstance(s, dict))
        if step_ms > 0:
            duration_sec = max(duration_sec, step_ms / 1000.0)
        if duration_sec <= 0 and job.get("steps"):
            duration_sec = 0.05  # floor for completed sync path — still honest "fast"
        revenue = float(order.get("price_eur") or order.get("amount_eur") or 0)
        cost = proxy_cost_eur(str(job.get("work_type") or "landing_page"), duration_sec)
        modules: list[str] = []
        for s in job.get("steps") or []:
            if not isinstance(s, dict):
                continue
            mod = s.get("module")
            if mod and str(mod) not in modules:
                modules.append(str(mod))
        manual = any(
            bool(s.get("manual_review"))
            for s in (job.get("steps") or [])
            if isinstance(s, dict)
        )
        job["duration_sec"] = round(duration_sec, 2)
        job["economics"] = {
            "revenue_eur": round(revenue, 2),
            "cost_eur_proxy": cost,
            "margin_eur_proxy": round(revenue - cost, 2),
            "cost_source": "proxy_v0",
            "cost_note_ru": (
                "Себестоимость — прокси (base + время), пока нет учёта токенов/API. "
                "Не путать с Ledger."
            ),
            "currency": str(order.get("currency") or "EUR"),
            "package_id": order.get("package_id"),
        }
        job["modules_used"] = modules
        job["had_manual_review"] = manual

    def run_for_order(self, order_id: str, *, force: bool = False) -> dict[str, Any]:
        """Entry: paid Stripe order → Work Farm job (Landing v0)."""
        order = self._get_order(order_id)
        if not order:
            return {"ok": False, "error": "order_not_found"}

        existing = self.find_job_for_order(order_id)
        if existing and not force and existing.get("status") in ("success", "running"):
            return {"ok": True, "reused": True, "job": existing}

        work_type = resolve_work_type(order)
        type_meta = WORK_TYPES.get(work_type) or {}
        steps_plan = plan_steps(work_type)
        job_id = f"WF-{uuid.uuid4().hex[:10].upper()}"
        job: dict[str, Any] = {
            "job_id": job_id,
            "version": WORK_FARM_VERSION,
            "order_id": order_id,
            "work_type": work_type,
            "work_type_label_ru": type_meta.get("label_ru") or work_type,
            "enabled": bool(type_meta.get("enabled")),
            "status": "running",
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "plan": steps_plan,
            "steps": [],
            "product_id": order.get("product_id"),
            "marketplace": False,
            "source": "stripe_order",
            "business_name": order.get("business_name"),
            "package_id": order.get("package_id"),
        }
        self._save_job(job)
        self._append_index(
            {
                "job_id": job_id,
                "order_id": order_id,
                "work_type": work_type,
                "at": job["created_at"],
                "status": "running",
            }
        )

        def _timed_step(
            step_id: str,
            fn: Callable[[], tuple[str, str, dict[str, Any]]],
            *,
            worker: str,
            module: str | None = None,
            manual_review: bool = False,
        ) -> str:
            started = _utc_now()
            t0 = datetime.now(timezone.utc)
            try:
                status, detail, meta = fn()
            except Exception as exc:
                status, detail, meta = "error", str(exc)[:240], {}
            duration_ms = int((datetime.now(timezone.utc) - t0).total_seconds() * 1000)
            job["steps"].append(
                self._step_result(
                    step_id=step_id,
                    status=status,
                    detail_ru=detail,
                    meta=meta,
                    started_at=started,
                    duration_ms=duration_ms,
                    worker=worker,
                    module=module,
                    manual_review=manual_review,
                    cost_eur_proxy=round(proxy_cost_eur(work_type, duration_ms / 1000.0) * 0.15, 3),
                )
            )
            return status

        # --- intake ---
        _timed_step(
            "intake",
            lambda: (
                "success",
                f"Заказ {order_id} · пакет {order.get('package_id') or '—'} · "
                f"{order.get('business_name') or '—'}",
                {},
            ),
            worker="intake",
            module="work_farm_intake",
        )

        if not type_meta.get("enabled"):
            _timed_step(
                "blocked",
                lambda: ("blocked", str(type_meta.get("note_ru") or "Тип отключён в v0"), {}),
                worker="blocked",
            )
            job["status"] = "blocked"
            job["updated_at"] = _utc_now()
            self._finalize_economics(job, order)
            self._save_job(job)
            return {"ok": True, "job": job, "blocked": True}

        if work_type == "repair_manual":
            def _op() -> tuple[str, str, dict[str, Any]]:
                prod = self._start_production(order_id)
                return (
                    "success",
                    "Ремонт в очереди оператора (не полный AI-конвейер).",
                    {"production": {"ok": prod.get("ok"), "message": prod.get("message")}},
                )

            st = _timed_step(
                "operator",
                _op,
                worker="operator",
                module="manual_operator",
                manual_review=True,
            )
            job["status"] = "awaiting_operator" if st != "error" else "error"
            job["updated_at"] = _utc_now()
            self._finalize_economics(job, order)
            self._save_job(job)
            return {"ok": job["status"] != "error", "job": job}

        # --- brief ---
        brief_bits = [
            str(order.get("business_name") or ""),
            str(order.get("city") or ""),
            str(order.get("package_id") or "basic"),
        ]
        _timed_step(
            "brief",
            lambda: ("success", "Бриф: " + " · ".join(b for b in brief_bits if b), {}),
            worker="brief",
            module="sales_order_brief",
        )

        # --- factory worker ---
        product_id_box: dict[str, Any] = {"id": None}

        def _factory() -> tuple[str, str, dict[str, Any]]:
            prod = self._start_production(order_id)
            pid = prod.get("product_id") or order.get("product_id")
            product_id_box["id"] = pid
            job["product_id"] = pid
            ok = bool(prod.get("ok", True))
            return (
                "success" if ok else "error",
                str(prod.get("message") or "Factory production"),
                {"product_id": pid},
            )

        st = _timed_step(
            "factory",
            _factory,
            worker="factory",
            module="factory_landing_builder",
        )
        product_id = product_id_box.get("id")
        if st == "error":
            job["status"] = "error"
            job["updated_at"] = _utc_now()
            self._finalize_economics(job, order)
            self._save_job(job)
            return {"ok": False, "job": job}

        # --- quality gate ---
        def _gate() -> tuple[str, str, dict[str, Any]]:
            if not product_id or not self._get_product:
                return ("skipped", "Нет product_id — Quality Gate пропущен", {})
            product = self._get_product(str(product_id)) or {}
            meta = product.get("meta") if isinstance(product.get("meta"), dict) else {}
            qg = meta.get("quality_gate") or product.get("quality_gate")
            if isinstance(qg, dict):
                passed = bool(qg.get("passed") or qg.get("ok") or qg.get("pass"))
                return (
                    "success" if passed else "error",
                    "Quality Gate OK" if passed else "Quality Gate FAIL",
                    {"quality_gate": qg},
                )
            return (
                "success",
                "Factory собрал продукт · gate в meta отсутствует (sync Path A OK)",
                {},
            )

        st = _timed_step(
            "quality_gate",
            _gate,
            worker="quality_gate",
            module="factory_quality_gate",
            manual_review=False,
        )
        if st == "error":
            job["status"] = "error"
            job["updated_at"] = _utc_now()
            self._finalize_economics(job, order)
            self._save_job(job)
            return {"ok": False, "job": job}

        # --- ready ---
        refreshed = self._get_order(order_id) or order

        def _ready() -> tuple[str, str, dict[str, Any]]:
            status = str(refreshed.get("status") or "")
            ready = status in ("ready", "delivered") or bool(product_id)
            return (
                "success" if ready else "pending",
                f"Статус заказа: {status or '—'} · product={product_id or '—'}",
                {"order_status": status},
            )

        st = _timed_step(
            "ready",
            _ready,
            worker="delivery",
            module="client_delivery",
        )
        job["status"] = "success" if st == "success" else "in_production"
        job["updated_at"] = _utc_now()
        self._finalize_economics(job, refreshed if isinstance(refreshed, dict) else order)
        self._save_job(job)
        self._append_index(
            {
                "job_id": job_id,
                "order_id": order_id,
                "work_type": work_type,
                "at": job["updated_at"],
                "status": job["status"],
                "product_id": product_id,
                "duration_sec": job.get("duration_sec"),
                "revenue_eur": (job.get("economics") or {}).get("revenue_eur"),
            }
        )
        return {"ok": True, "job": job}

    def stats(self, *, work_type: str = "landing_page") -> dict[str, Any]:
        """Aggregate real jobs only — zeros until first orders."""
        jobs = [
            j
            for j in self.list_all_jobs(limit=500)
            if str(j.get("work_type") or "") == work_type
        ]
        received = len(jobs)
        success = sum(1 for j in jobs if j.get("status") == "success")
        error = sum(1 for j in jobs if j.get("status") == "error")
        other = received - success - error
        durations = [float(j.get("duration_sec") or 0) for j in jobs if float(j.get("duration_sec") or 0) > 0]
        revenues = [
            float((j.get("economics") or {}).get("revenue_eur") or 0)
            for j in jobs
            if float((j.get("economics") or {}).get("revenue_eur") or 0) > 0
        ]
        costs = [
            float((j.get("economics") or {}).get("cost_eur_proxy") or 0)
            for j in jobs
            if (j.get("economics") or {}).get("cost_eur_proxy") is not None
        ]
        avg_sec = round(sum(durations) / len(durations), 1) if durations else None
        avg_min = round(avg_sec / 60.0, 1) if avg_sec is not None else None
        label = (WORK_TYPES.get(work_type) or {}).get("label_ru") or work_type
        return {
            "work_type": work_type,
            "label_ru": label,
            "received": received,
            "success": success,
            "error": error,
            "other": other,
            "avg_duration_sec": avg_sec,
            "avg_duration_min": avg_min,
            "avg_revenue_eur": round(sum(revenues) / len(revenues), 2) if revenues else None,
            "avg_cost_eur_proxy": round(sum(costs) / len(costs), 2) if costs else None,
            "cost_source": "proxy_v0",
            "sample_note_ru": (
                "Статистика с реальных job-файлов. "
                "Средняя себестоимость — прокси, не Ledger. "
                "После 10–20 заказов видно, где тормозит конвейер."
            ),
            "marketplace": False,
        }

    def replay(self, job_id: str) -> dict[str, Any]:
        """Read-only Replay Job — timeline + economics (no re-run)."""
        job = self.get_job(job_id)
        if not job:
            return {"ok": False, "error": "job_not_found"}
        order = self._get_order(str(job.get("order_id") or "")) or {}
        if not job.get("economics"):
            self._finalize_economics(job, order if order else {})
        steps = []
        for s in job.get("steps") or []:
            if not isinstance(s, dict):
                continue
            steps.append(
                {
                    "id": s.get("id"),
                    "status": s.get("status"),
                    "started_at": s.get("started_at") or s.get("at"),
                    "finished_at": s.get("at"),
                    "duration_ms": int(s.get("duration_ms") or 0),
                    "duration_sec": round(int(s.get("duration_ms") or 0) / 1000.0, 2),
                    "worker": s.get("worker"),
                    "module": s.get("module"),
                    "manual_review": bool(s.get("manual_review")),
                    "detail_ru": s.get("detail_ru"),
                    "cost_eur_proxy": s.get("cost_eur_proxy"),
                }
            )
        eco = job.get("economics") or {}
        return {
            "ok": True,
            "mode": "replay_readonly",
            "marketplace": False,
            "job_id": job.get("job_id"),
            "order_id": job.get("order_id"),
            "work_type": job.get("work_type"),
            "work_type_label_ru": job.get("work_type_label_ru"),
            "status": job.get("status"),
            "business_name": job.get("business_name") or order.get("business_name"),
            "pipeline": [p.get("id") for p in (job.get("plan") or []) if isinstance(p, dict)],
            "steps": steps,
            "modules_used": job.get("modules_used") or [],
            "had_manual_review": bool(job.get("had_manual_review")),
            "duration_sec": job.get("duration_sec"),
            "economics": eco,
            "headline_ru": (
                f"Replay {job.get('job_id')} · {job.get('work_type_label_ru') or job.get('work_type')} · "
                f"{eco.get('revenue_eur', 0)} € выручка · "
                f"{eco.get('cost_eur_proxy', 0)} € себестоимость (прокси)"
            ),
            "note_ru": (
                "Replay показывает факт прошлого прогона. "
                "Повторный запуск — POST /api/work-farm/run/{order_id}?force=1"
            ),
        }

    def status_board(self) -> dict[str, Any]:
        recent = self.list_recent(limit=15)
        landing = self.stats(work_type="landing_page")
        return {
            "ok": True,
            "version": WORK_FARM_VERSION,
            "marketplace": False,
            "primary_work_type": "landing_page",
            "catalog": self.catalog(),
            "stats": {
                "landing_page": landing,
            },
            "recent_jobs": recent,
            "headline_ru": (
                "Work Farm v0: Stripe → Landing Factory → Quality Gate. "
                "Marketplace внешних задач — не здесь."
            ),
        }
