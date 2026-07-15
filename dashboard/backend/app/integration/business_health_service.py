"""Mission 2 — Business Health: CEO funnel, KPIs, weekly review (no LLM)."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.integration.opportunity_discovery_engine import (
    _pick_service,
    load_lost_reasons,
    lost_reason_database,
)
from app.integration.product_line import service_label_ru

_MISSION2_TARGETS = {
    "conversations": 10,
    "proposals": 3,
    "payments": 1,
    "repeats": 1,
}

_CONVERSATION_STATUSES = frozenset({"contacted", "replied", "qualified", "won", "lost"})
_PROPOSAL_STATUSES = frozenset({"proposed", "qualified", "won"})

_MANUAL_FIELDS = frozenset({"conversations", "proposals", "payments", "repeats"})


def _default_manual() -> dict[str, int]:
    return {"conversations": 0, "proposals": 0, "payments": 0, "repeats": 0}


class BusinessHealthService:
    def __init__(
        self,
        memory_dir: Path,
        opportunity: object,
    ) -> None:
        self._memory = memory_dir
        self._opportunity = opportunity
        self._memory.mkdir(parents=True, exist_ok=True)

    def _manual_path(self) -> Path:
        return self._memory / "mission2_manual.json"

    def _finance_snapshot(self) -> dict[str, Any]:
        path = self._memory / "finance_snapshot.json"
        if not path.is_file():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _load_manual(self) -> dict[str, int]:
        path = self._manual_path()
        if not path.is_file():
            return _default_manual()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return _default_manual()
        out = _default_manual()
        for key in _MANUAL_FIELDS:
            out[key] = max(0, int(raw.get(key) or 0))
        return out

    def _save_manual(self, data: dict[str, int]) -> None:
        path = self._manual_path()
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None

    @staticmethod
    def _week_start(now: datetime | None = None) -> datetime:
        now = now or datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
        return start

    @staticmethod
    def _yesterday_start(now: datetime | None = None) -> tuple[datetime, datetime]:
        now = now or datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return today - timedelta(days=1), today

    def _service_for_row(self, row: dict[str, Any]) -> tuple[str, str]:
        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        if meta.get("service_id"):
            sid = str(meta["service_id"])
            return sid, service_label_ru(sid, fallback=sid)
        analysis = row.get("site_analysis") if isinstance(row.get("site_analysis"), dict) else {}
        issues = [str(i) for i in (analysis.get("issues") or []) if str(i).strip()]
        svc_id, label, _ = _pick_service(issues, len(issues))
        return svc_id, label

    def _auto_counts(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        conversations = sum(1 for r in rows if r.get("status") in _CONVERSATION_STATUSES)
        proposals = sum(1 for r in rows if r.get("status") in _PROPOSAL_STATUSES)
        payments = sum(1 for r in rows if r.get("status") == "won")
        by_company: dict[str, int] = {}
        for r in rows:
            if r.get("status") != "won":
                continue
            key = str(r.get("company_name") or r.get("id") or "").strip().lower()
            if key:
                by_company[key] = by_company.get(key, 0) + 1
        repeats = sum(1 for n in by_company.values() if n > 1)
        return {
            "conversations": conversations,
            "proposals": proposals,
            "payments": payments,
            "repeats": repeats,
        }

    def _week_funnel(self, rows: list[dict[str, Any]], *, week_start: datetime) -> dict[str, Any]:
        found = 0
        talks = 0
        proposals = 0
        deals = 0
        revenue = 0.0
        for row in rows:
            found_at = self._parse_dt(str(row.get("found_at") or ""))
            updated_at = self._parse_dt(str(row.get("updated_at") or row.get("found_at") or ""))
            status = str(row.get("status") or "")
            if found_at and found_at >= week_start:
                found += 1
            if updated_at and updated_at >= week_start:
                if status in _CONVERSATION_STATUSES:
                    talks += 1
                if status in _PROPOSAL_STATUSES:
                    proposals += 1
                if status == "won":
                    deals += 1
                    revenue += float(row.get("revenue_eur") or 0)
        return {
            "companies_found": found,
            "conversations": talks,
            "proposals": proposals,
            "deals": deals,
            "revenue_eur": round(revenue, 2),
        }

    def _weekly_review(self, rows: list[dict[str, Any]], *, week_start: datetime) -> dict[str, Any]:
        won_by: dict[str, int] = {}
        lost_by: dict[str, int] = {}
        pipeline_by: dict[str, int] = {}

        for row in rows:
            updated_at = self._parse_dt(str(row.get("updated_at") or row.get("found_at") or ""))
            if updated_at and updated_at < week_start:
                continue
            svc_id, label = self._service_for_row(row)
            status = str(row.get("status") or "")
            if status == "won":
                won_by[label] = won_by.get(label, 0) + 1
            elif status == "lost":
                lost_by[label] = lost_by.get(label, 0) + 1
            elif status not in ("new", "reviewed"):
                pipeline_by[label] = pipeline_by.get(label, 0) + 1

        def _top(d: dict[str, int], fallback: str) -> str:
            if not d:
                return fallback
            return max(d.items(), key=lambda x: x[1])[0]

        lost_db = lost_reason_database(self._memory)
        top_reason = lost_db["by_reason"][0] if lost_db["by_reason"] else None
        best = _top(won_by, "Пока нет побед — фиксируйте разговоры в журнале")
        worst = _top(lost_by, "Отказов мало — продолжайте обзвон")

        if top_reason and top_reason["code"] == "expensive":
            recommendation = "Попробовать пакет до 250 € — частая причина отказов «Дорого»"
        elif won_by:
            recommendation = f"Удвоить оффер «{best}» — он уже приносит победы"
        elif pipeline_by:
            top_pipe = max(pipeline_by.items(), key=lambda x: x[1])[0]
            recommendation = f"Дожать предложения по «{top_pipe}» — больше всего в работе"
        else:
            recommendation = "Запустить ферму и отметить 3 разговора в журнале — без данных рынок молчит"

        return {
            "period_label_ru": "На этой неделе",
            "best_seller_ru": best,
            "worst_seller_ru": worst,
            "top_rejection_ru": top_reason["label_ru"] if top_reason else "Пока нет записей",
            "top_rejection_count": top_reason["count"] if top_reason else 0,
            "recommendation_ru": recommendation,
        }

    def _morning_brief(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        y_start, y_end = self._yesterday_start()
        new_y = 0
        lost_y = 0
        last_reason: str | None = None
        for row in rows:
            found_at = self._parse_dt(str(row.get("found_at") or ""))
            updated_at = self._parse_dt(str(row.get("updated_at") or ""))
            if found_at and y_start <= found_at < y_end:
                new_y += 1
            if updated_at and y_start <= updated_at < y_end and row.get("status") == "lost":
                lost_y += 1
                meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
                last_reason = str(meta.get("lost_reason_ru") or "не указана")[:120]

        active = [
            r
            for r in rows
            if r.get("status") not in ("won", "lost")
            and int(r.get("score") or 0) >= 50
        ]
        active.sort(key=lambda r: (-int(r.get("score") or 0), str(r.get("company_name") or "")))
        pick = active[0] if active else None
        if pick:
            rec = f"Связаться с {pick.get('company_name') or 'лидом из журнала'} — выше среднего по score"
        else:
            rec = "Запустить ферму и взять 1 карточку из журнала в работу"

        lines: list[dict[str, Any]] = []
        if new_y:
            lines.append({"text": f"Вчера: {new_y} новых возможностей.", "highlight": True})
        if lost_y:
            reason = last_reason or "не указана"
            lines.append({"text": f"Вчера: {lost_y} отказ(ов). Причина — {reason}.", "highlight": False})
        if not lines:
            lines.append({"text": "Вчера новых событий в журнале не было.", "highlight": False})

        return {
            "headline_ru": "Доброе утро.",
            "lines_ru": lines,
            "recommendation_ru": f"Сегодня рекомендую: {rec}",
        }

    def bump_manual(self, field: str, delta: int = 1) -> dict[str, Any]:
        if field not in _MANUAL_FIELDS:
            raise ValueError("invalid_field")
        manual = self._load_manual()
        manual[field] = max(0, manual[field] + int(delta))
        self._save_manual(manual)
        return self.dashboard()

    def dashboard(self) -> dict[str, Any]:
        rows = self._opportunity.list_opportunities(limit=5000)
        manual = self._load_manual()
        auto = self._auto_counts(rows)
        week_start = self._week_start()
        funnel = self._week_funnel(rows, week_start=week_start)

        kpis: dict[str, Any] = {}
        for key, target in _MISSION2_TARGETS.items():
            current = auto[key] + manual[key]
            kpis[key] = {
                "current": current,
                "target": target,
                "auto": auto[key],
                "manual": manual[key],
                "progress_pct": min(100, round(100 * current / target)) if target else 100,
            }

        finance_snap = self._finance_snapshot()
        net_profit = float(finance_snap.get("net_profit_eur") or 0)
        demo = bool(finance_snap.get("demo_mode"))
        if funnel["revenue_eur"] > 0 and net_profit <= 0 and not demo:
            net_profit = round(funnel["revenue_eur"] * 0.72, 2)

        funnel["net_profit_eur"] = round(net_profit, 2) if funnel["deals"] else 0.0

        lost_total = len(load_lost_reasons(self._memory))
        confidence_note = (
            "Цифры из журнала фермы + ручной учёт полевых звонков. "
            "Без записей в журнале рынок не виден."
        )

        return {
            "mission": "Mission 2 — поиск рынка",
            "date": date.today().isoformat(),
            "week_start": week_start.date().isoformat(),
            "kpi_note_ru": confidence_note,
            "kpis": kpis,
            "kpi_labels_ru": {
                "conversations": "Разговоры",
                "proposals": "Предложения",
                "payments": "Оплаты",
                "repeats": "Повторы",
            },
            "funnel_week": funnel,
            "funnel_steps_ru": [
                "компаний найдено",
                "разговоров",
                "предложений",
                "договоров",
                "€ выручка",
                "чистая прибыль",
            ],
            "weekly_review": self._weekly_review(rows, week_start=week_start),
            "morning_brief": self._morning_brief(rows),
            "market_signal": {
                "opportunities_total": len(rows),
                "lost_reasons_logged": lost_total,
                "pipeline_active": sum(1 for r in rows if r.get("status") not in ("won", "lost")),
                "data_honesty_ru": (
                    "Гипотеза рынка подтверждается только реальными разговорами и оплатами."
                ),
            },
            "links": {
                "farm": "/",
                "journal": "/journal",
                "finance": "/finance",
            },
        }
