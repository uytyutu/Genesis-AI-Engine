"""Opportunity Engine v0 — universal opportunities, source adapters, honest journal.

Skeleton only: manual + google_maps adapters (no auto-search, no auto-outreach).
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_OPPORTUNITY_TYPES = {
    "lead": "Клиент / заказчик",
    "partner": "Партнёр",
    "marketplace": "Площадка",
    "tender": "Тендер",
    "job": "Сотрудник",
    "trend": "Тренд",
    "idea": "Идея услуги",
    "investment": "Инвестиция",
}

_STATUSES = {
    "new": "Новая",
    "reviewed": "Просмотрена",
    "proposed": "Предложение готово",
    "contacted": "Связались",
    "replied": "Ответили",
    "qualified": "Заявка",
    "won": "Продажа",
    "lost": "Отказ",
}

_SOURCE_REGISTRY: dict[str, dict[str, Any]] = {
    "manual": {
        "id": "manual",
        "label": "Ручной ввод",
        "adapter": "manual",
        "enabled": True,
        "auto_search": False,
    },
    "google_maps": {
        "id": "google_maps",
        "label": "Google Maps",
        "adapter": "google_maps",
        "enabled": True,
        "auto_search": False,
    },
    "google_business": {
        "id": "google_business",
        "label": "Google Business",
        "adapter": "google_business",
        "enabled": False,
        "auto_search": False,
    },
    "reddit": {
        "id": "reddit",
        "label": "Reddit",
        "adapter": "reddit",
        "enabled": False,
        "auto_search": False,
    },
    "facebook": {
        "id": "facebook",
        "label": "Facebook",
        "adapter": "facebook",
        "enabled": False,
        "auto_search": False,
    },
    "linkedin": {
        "id": "linkedin",
        "label": "LinkedIn",
        "adapter": "linkedin",
        "enabled": False,
        "auto_search": False,
    },
    "telegram": {
        "id": "telegram",
        "label": "Telegram",
        "adapter": "telegram",
        "enabled": False,
        "auto_search": False,
    },
    "x": {
        "id": "x",
        "label": "X",
        "adapter": "x",
        "enabled": False,
        "auto_search": False,
    },
    "email": {
        "id": "email",
        "label": "Email",
        "adapter": "email",
        "enabled": False,
        "auto_search": False,
    },
    "seo": {
        "id": "seo",
        "label": "SEO",
        "adapter": "seo",
        "enabled": False,
        "auto_search": False,
    },
    "referrals": {
        "id": "referrals",
        "label": "Рекомендации",
        "adapter": "referrals",
        "enabled": False,
        "auto_search": False,
    },
}


class OpportunityService:
    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._memory.mkdir(parents=True, exist_ok=True)
        self._ensure_engine_config()

    def _config_path(self) -> Path:
        return self._memory / "opportunity_engine.json"

    def _queue_path(self) -> Path:
        return self._memory / "opportunities.jsonl"

    def _ensure_engine_config(self) -> None:
        path = self._config_path()
        if path.is_file():
            return
        path.write_text(
            json.dumps(
                {"version": 1, "sources": _SOURCE_REGISTRY},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def _load_config(self) -> dict:
        try:
            data = json.loads(self._config_path().read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {"version": 1, "sources": dict(_SOURCE_REGISTRY)}
        sources = {**_SOURCE_REGISTRY, **(data.get("sources") or {})}
        return {"version": data.get("version", 1), "sources": sources}

    def _load_rows(self) -> list[dict]:
        path = self._queue_path()
        if not path.is_file():
            return []
        rows: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(self._normalize_row(json.loads(line)))
                except json.JSONDecodeError:
                    continue
        return rows

    def _normalize_row(self, row: dict) -> dict:
        """Migrate legacy opportunity rows to v0 schema."""
        status = row.get("status", "new")
        legacy_map = {
            "used": "contacted",
            "pending_owner": "proposed",
            "prepared": "reviewed",
            "client_won": "won",
        }
        status = legacy_map.get(status, status)
        if status not in _STATUSES:
            status = "new"

        opp_type = row.get("opportunity_type") or "lead"
        if opp_type not in _OPPORTUNITY_TYPES:
            opp_type = "lead"

        source_id = row.get("source_id") or row.get("source") or "manual"
        company = row.get("company_name") or row.get("title") or ""
        interactions = row.get("interactions")
        if not isinstance(interactions, list):
            interactions = []
        site_analysis = row.get("site_analysis")
        if site_analysis is not None and not isinstance(site_analysis, dict):
            site_analysis = None
        return {
            "id": row.get("id") or f"opp-{uuid.uuid4().hex[:10]}",
            "opportunity_type": opp_type,
            "source_id": source_id,
            "company_name": company,
            "contact": row.get("contact") or "",
            "fit_reason": row.get("fit_reason") or "",
            "score": int(row.get("score") or 0),
            "status": status,
            "status_label": _STATUSES.get(status, status),
            "proposed_message": row.get("proposed_message") or "",
            "notes": row.get("notes") or "",
            "potential_value_eur": float(row.get("potential_value_eur") or 0),
            "revenue_eur": float(row.get("revenue_eur") or 0),
            "found_at": row.get("found_at") or datetime.now(timezone.utc).isoformat(),
            "updated_at": row.get("updated_at") or row.get("found_at") or datetime.now(timezone.utc).isoformat(),
            "meta": row.get("meta") if isinstance(row.get("meta"), dict) else {},
            "website_url": row.get("website_url") or "",
            "site_analysis": site_analysis,
            "recommended_package_id": row.get("recommended_package_id") or "",
            "recommended_price_eur": float(row.get("recommended_price_eur") or 0),
            "pricing_rationale": row.get("pricing_rationale") or "",
            "email_subject": row.get("email_subject") or "",
            "outreach_status": row.get("outreach_status") or "none",
            "interactions": interactions,
        }

    def _save_rows(self, rows: list[dict]) -> None:
        path = self._queue_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _append_row(self, row: dict) -> dict:
        with open(self._queue_path(), "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def _today_iso(self) -> str:
        return date.today().isoformat()

    def _is_today(self, iso: str) -> bool:
        return str(iso)[:10] == self._today_iso()

    def list_sources(self) -> list[dict]:
        cfg = self._load_config()
        out: list[dict] = []
        for source_id, meta in cfg["sources"].items():
            base = _SOURCE_REGISTRY.get(source_id, {})
            merged = {**base, **meta, "id": source_id}
            out.append(
                {
                    "id": source_id,
                    "label": merged.get("label", source_id),
                    "adapter": merged.get("adapter", source_id),
                    "enabled": bool(merged.get("enabled")),
                    "auto_search": bool(merged.get("auto_search")),
                }
            )
        return sorted(out, key=lambda s: (not s["enabled"], s["label"]))

    def list_types(self) -> list[dict]:
        return [{"id": k, "label": v} for k, v in _OPPORTUNITY_TYPES.items()]

    def list_statuses(self) -> list[dict]:
        return [{"id": k, "label": v} for k, v in _STATUSES.items()]

    def _source_enabled(self, source_id: str) -> bool:
        cfg = self._load_config()
        src = cfg["sources"].get(source_id) or _SOURCE_REGISTRY.get(source_id)
        if not src:
            return False
        return bool(src.get("enabled"))

    def _estimate_score(self, fit_reason: str, potential_value_eur: float) -> int:
        score = 40
        reason = fit_reason.lower()
        if any(w in reason for w in ("нет сайта", "no website", "устарел", "outdated")):
            score += 25
        if any(w in reason for w in ("отзыв", "рейтинг", "maps", "google")):
            score += 10
        if potential_value_eur >= 650:
            score += 15
        elif potential_value_eur >= 350:
            score += 8
        return min(100, max(0, score))

    def create(self, payload: dict) -> dict:
        source_id = (payload.get("source_id") or "manual").strip()
        if not self._source_enabled(source_id):
            raise ValueError("source_disabled")

        company = (payload.get("company_name") or "").strip()
        if not company:
            raise ValueError("company_required")

        opp_type = (payload.get("opportunity_type") or "lead").strip()
        if opp_type not in _OPPORTUNITY_TYPES:
            raise ValueError("invalid_type")

        now = datetime.now(timezone.utc).isoformat()
        potential = float(payload.get("potential_value_eur") or 0)
        fit_reason = (payload.get("fit_reason") or "").strip()
        score = payload.get("score")
        if score is None:
            score = self._estimate_score(fit_reason, potential)

        row = {
            "id": f"opp-{uuid.uuid4().hex[:10]}",
            "opportunity_type": opp_type,
            "source_id": source_id,
            "company_name": company,
            "contact": (payload.get("contact") or "").strip(),
            "fit_reason": fit_reason,
            "score": int(score),
            "status": "new",
            "status_label": _STATUSES["new"],
            "proposed_message": (payload.get("proposed_message") or "").strip(),
            "notes": (payload.get("notes") or "").strip(),
            "potential_value_eur": potential,
            "revenue_eur": 0.0,
            "found_at": now,
            "updated_at": now,
            "meta": payload.get("meta") if isinstance(payload.get("meta"), dict) else {},
            "website_url": (payload.get("website_url") or "").strip(),
            "site_analysis": None,
            "recommended_package_id": "",
            "recommended_price_eur": 0.0,
            "pricing_rationale": "",
            "email_subject": "",
            "outreach_status": "none",
            "interactions": [],
        }
        return self._append_row(row)

    def list_opportunities(
        self,
        *,
        source_id: str | None = None,
        status: str | None = None,
        today_only: bool = False,
        limit: int = 100,
    ) -> list[dict]:
        rows = self._load_rows()
        if source_id:
            rows = [r for r in rows if r.get("source_id") == source_id]
        if status:
            rows = [r for r in rows if r.get("status") == status]
        if today_only:
            rows = [r for r in rows if self._is_today(str(r.get("found_at", "")))]
        rows.sort(key=lambda r: (int(r.get("score") or 0), r.get("found_at", "")), reverse=True)
        return rows[:limit]

    def get(self, opportunity_id: str) -> dict | None:
        for row in self._load_rows():
            if row.get("id") == opportunity_id:
                return row
        return None

    def update(self, opportunity_id: str, payload: dict) -> dict:
        rows = self._load_rows()
        found: dict | None = None
        for i, row in enumerate(rows):
            if row.get("id") != opportunity_id:
                continue
            if "status" in payload:
                status = payload["status"]
                if status not in _STATUSES:
                    raise ValueError("invalid_status")
                row["status"] = status
                row["status_label"] = _STATUSES[status]
            for field in (
                "proposed_message",
                "notes",
                "contact",
                "fit_reason",
                "company_name",
                "website_url",
                "pricing_rationale",
                "email_subject",
                "outreach_status",
                "recommended_package_id",
            ):
                if field in payload:
                    row[field] = str(payload[field] or "").strip()
            if "site_analysis" in payload:
                val = payload["site_analysis"]
                row["site_analysis"] = val if isinstance(val, dict) else None
            if "interactions" in payload and isinstance(payload["interactions"], list):
                row["interactions"] = payload["interactions"]
            if "score" in payload:
                row["score"] = int(payload["score"])
            if "potential_value_eur" in payload:
                row["potential_value_eur"] = float(payload["potential_value_eur"])
            if "recommended_price_eur" in payload:
                row["recommended_price_eur"] = float(payload["recommended_price_eur"])
            if "revenue_eur" in payload:
                row["revenue_eur"] = float(payload["revenue_eur"])
            row["updated_at"] = datetime.now(timezone.utc).isoformat()
            rows[i] = row
            found = row
            break
        if found is None:
            raise ValueError("not_found")
        self._save_rows(rows)
        return found

    def morning_dashboard(self) -> dict:
        rows = self._load_rows()
        today_rows = [r for r in rows if self._is_today(str(r.get("found_at", "")))]
        sources = self.list_sources()
        enabled_ids = {s["id"] for s in sources if s["enabled"]}

        by_source: list[dict] = []
        total_today = 0
        for src in sources:
            count = sum(1 for r in today_rows if r.get("source_id") == src["id"])
            by_source.append(
                {
                    "source_id": src["id"],
                    "label": src["label"],
                    "enabled": src["enabled"],
                    "count_today": count,
                }
            )
            if src["enabled"]:
                total_today += count

        potential_value = sum(
            float(r.get("potential_value_eur") or 0)
            for r in today_rows
            if r.get("source_id") in enabled_ids
        )

        top = self.list_opportunities(today_only=True, limit=10)
        active_pipeline = [
            r for r in rows if r.get("status") not in ("won", "lost")
        ]

        return {
            "date": self._today_iso(),
            "total_today": total_today,
            "potential_value_eur": round(potential_value, 2),
            "sources_today": by_source,
            "pipeline_count": len(active_pipeline),
            "won_count": sum(1 for r in rows if r.get("status") == "won"),
            "revenue_eur": round(
                sum(float(r.get("revenue_eur") or 0) for r in rows if r.get("status") == "won"),
                2,
            ),
            "top_today": top,
            "kpi_note": (
                "Только реальные записи журнала. Автопоиск и автосообщения выключены в v0."
            ),
        }

    def snapshot(self, revenue_today_eur: float = 0.0, clients: int = 0) -> dict:
        rows = self._load_rows()
        today = self._today_iso()
        dashboard = self.morning_dashboard()
        found_today = dashboard["total_today"]
        used_today = sum(
            1
            for r in rows
            if self._is_today(str(r.get("updated_at", "")))
            and r.get("status") in ("contacted", "proposed", "replied", "qualified", "won")
        )
        pending_owner = sum(
            1
            for r in rows
            if r.get("status") in ("new", "reviewed", "proposed")
            or r.get("outreach_status") == "pending_approval"
        )
        prepared = sum(1 for r in rows if r.get("status") in ("proposed", "reviewed"))
        clients_won = sum(1 for r in rows if r.get("status") == "won")
        revenue_from_opps = sum(
            float(r.get("revenue_eur", 0) or 0) for r in rows if r.get("status") == "won"
        )

        engine_active = bool(rows)

        if not engine_active:
            status_message = (
                "Скелет готов. Добавьте первую реальную возможность — ручной ввод или Google Maps."
            )
            queue_preview: list[dict] = []
        else:
            status_message = (
                f"Сегодня: {found_today} · в работе: {dashboard['pipeline_count']} · "
                f"потенциал: {dashboard['potential_value_eur']:.0f} €"
            )
            queue_preview = [
                {
                    "id": r.get("id"),
                    "title": r.get("company_name", "Возможность"),
                    "status": r.get("status", "new"),
                    "source_id": r.get("source_id"),
                    "score": r.get("score"),
                }
                for r in dashboard["top_today"][:5]
            ]

        return {
            "engine_active": engine_active,
            "department_label": "Opportunity Engine",
            "status_message": status_message,
            "found_today": found_today,
            "used_today": used_today,
            "clients_from_opportunities": clients_won if engine_active else clients,
            "revenue_from_opportunities_eur": revenue_from_opps if engine_active else revenue_today_eur,
            "pending_owner_approval": pending_owner,
            "prepared_count": prepared,
            "queue_preview": queue_preview,
            "sources_today": dashboard["sources_today"],
            "potential_value_eur": dashboard["potential_value_eur"],
            "kpi_note": dashboard["kpi_note"],
        }

    def record_opportunity(self, title: str, source: str, meta: dict | None = None) -> dict:
        """Legacy helper — maps to create()."""
        return self.create(
            {
                "company_name": title,
                "source_id": source if source in _SOURCE_REGISTRY else "manual",
                "fit_reason": (meta or {}).get("fit_reason", ""),
                "contact": (meta or {}).get("contact", ""),
                "meta": meta or {},
            }
        )
