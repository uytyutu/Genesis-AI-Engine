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


def _job_path(memory_dir: Path, job_id: str) -> Path:
    root = Path(memory_dir) / "work_farm" / "jobs"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{job_id}.json"


def _index_path(memory_dir: Path) -> Path:
    root = Path(memory_dir) / "work_farm"
    root.mkdir(parents=True, exist_ok=True)
    return root / "index.jsonl"


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

    def _step_result(
        self,
        *,
        step_id: str,
        status: str,
        detail_ru: str = "",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "id": step_id,
            "status": status,  # success | error | skipped | pending | blocked
            "at": _utc_now(),
            "detail_ru": detail_ru,
            "meta": meta or {},
        }

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

        # --- intake ---
        job["steps"].append(
            self._step_result(
                step_id="intake",
                status="success",
                detail_ru=f"Заказ {order_id} · пакет {order.get('package_id') or '—'} · "
                f"{order.get('business_name') or '—'}",
            )
        )

        if not type_meta.get("enabled"):
            job["steps"].append(
                self._step_result(
                    step_id="blocked",
                    status="blocked",
                    detail_ru=str(type_meta.get("note_ru") or "Тип отключён в v0"),
                )
            )
            job["status"] = "blocked"
            job["updated_at"] = _utc_now()
            self._save_job(job)
            return {"ok": True, "job": job, "blocked": True}

        if work_type == "repair_manual":
            try:
                prod = self._start_production(order_id)
                job["steps"].append(
                    self._step_result(
                        step_id="operator",
                        status="success",
                        detail_ru="Ремонт в очереди оператора (не полный AI-конвейер).",
                        meta={"production": {"ok": prod.get("ok"), "message": prod.get("message")}},
                    )
                )
                job["status"] = "awaiting_operator"
            except Exception as exc:
                job["steps"].append(
                    self._step_result(
                        step_id="operator",
                        status="error",
                        detail_ru=str(exc)[:240],
                    )
                )
                job["status"] = "error"
            job["updated_at"] = _utc_now()
            self._save_job(job)
            return {"ok": job["status"] != "error", "job": job}

        # --- brief ---
        brief_bits = [
            str(order.get("business_name") or ""),
            str(order.get("city") or ""),
            str(order.get("package_id") or "basic"),
        ]
        job["steps"].append(
            self._step_result(
                step_id="brief",
                status="success",
                detail_ru="Бриф: " + " · ".join(b for b in brief_bits if b),
            )
        )

        # --- factory worker ---
        product_id = None
        try:
            prod = self._start_production(order_id)
            product_id = prod.get("product_id") or order.get("product_id")
            job["product_id"] = product_id
            job["steps"].append(
                self._step_result(
                    step_id="factory",
                    status="success" if prod.get("ok", True) else "error",
                    detail_ru=str(prod.get("message") or "Factory production"),
                    meta={"product_id": product_id},
                )
            )
            if not prod.get("ok", True) and prod.get("error"):
                job["status"] = "error"
        except Exception as exc:
            job["steps"].append(
                self._step_result(
                    step_id="factory",
                    status="error",
                    detail_ru=str(exc)[:240],
                )
            )
            job["status"] = "error"
            job["updated_at"] = _utc_now()
            self._save_job(job)
            return {"ok": False, "job": job}

        # --- quality gate ---
        gate_status = "skipped"
        gate_detail = "Нет product_id — Quality Gate пропущен"
        gate_meta: dict[str, Any] = {}
        if product_id and self._get_product:
            try:
                product = self._get_product(str(product_id)) or {}
                meta = product.get("meta") if isinstance(product.get("meta"), dict) else {}
                qg = meta.get("quality_gate") or product.get("quality_gate")
                if isinstance(qg, dict):
                    passed = bool(qg.get("passed") or qg.get("ok") or qg.get("pass"))
                    gate_status = "success" if passed else "error"
                    gate_detail = "Quality Gate OK" if passed else "Quality Gate FAIL"
                    gate_meta = {"quality_gate": qg}
                else:
                    gate_status = "success"
                    gate_detail = "Factory собрал продукт · gate в meta отсутствует (считаем sync Path A OK)"
            except Exception as exc:
                gate_status = "error"
                gate_detail = str(exc)[:200]
        job["steps"].append(
            self._step_result(
                step_id="quality_gate",
                status=gate_status,
                detail_ru=gate_detail,
                meta=gate_meta,
            )
        )
        if gate_status == "error":
            job["status"] = "error"
            job["updated_at"] = _utc_now()
            self._save_job(job)
            return {"ok": False, "job": job}

        # --- ready / delivery handoff ---
        refreshed = self._get_order(order_id) or order
        status = str(refreshed.get("status") or "")
        ready = status in ("ready", "delivered") or bool(product_id)
        job["steps"].append(
            self._step_result(
                step_id="ready",
                status="success" if ready else "pending",
                detail_ru=f"Статус заказа: {status or '—'} · product={product_id or '—'}",
            )
        )
        job["status"] = "success" if ready else "in_production"
        job["updated_at"] = _utc_now()
        self._save_job(job)
        self._append_index(
            {
                "job_id": job_id,
                "order_id": order_id,
                "work_type": work_type,
                "at": job["updated_at"],
                "status": job["status"],
                "product_id": product_id,
            }
        )
        return {"ok": True, "job": job}

    def status_board(self) -> dict[str, Any]:
        recent = self.list_recent(limit=15)
        return {
            "ok": True,
            "version": WORK_FARM_VERSION,
            "marketplace": False,
            "primary_work_type": "landing_page",
            "catalog": self.catalog(),
            "recent_jobs": recent,
            "headline_ru": (
                "Work Farm v0: Stripe → Landing Factory → Quality Gate. "
                "Marketplace внешних задач — не здесь."
            ),
        }
