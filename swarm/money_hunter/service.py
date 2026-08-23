"""Money Hunter façade — import, approve, plan, delivery, reality snapshot."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from swarm.money_hunter.models import SOURCE_ADAPTERS, TASK_TEMPLATES
from swarm.money_hunter.store import MoneyHunterStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MoneyHunterService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)
        self._store = MoneyHunterStore(self._memory)

    def panel(self) -> dict[str, Any]:
        reality = self.reality()
        top = self.top(limit=12)
        return {
            "ok": True,
            "title": "MONEY HUNTER",
            "rule_ru": (
                "REAL REVENUE только из подтверждённого settlement. "
                "Pipeline / Toloka balance / estimates ≠ деньги."
            ),
            "first_money_mode": True,
            "first_money_ru": "Приоритет €30–€150 · low complexity · high automation · fast payment",
            "sources": SOURCE_ADAPTERS,
            "task_templates": list(TASK_TEMPLATES),
            "reality": reality,
            "top": top,
            "pipeline": self._pipeline_counts(),
            "auto_spend_policy": {
                "0_50": "pending_approval",
                "50_plus": "manual_approval",
                "500_plus": "ceo_explicit",
                "note_ru": "Никакой auto-spend без approval (Toloka / API / ads / cloud).",
            },
        }

    def _pipeline_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {
            "discovered": 0,
            "qualified": 0,
            "pending_approval": 0,
            "approved": 0,
            "executing": 0,
            "delivered": 0,
            "payment_pending": 0,
            "paid": 0,
            "rejected": 0,
        }
        for row in self._store.list_all():
            st = str(row.get("status") or "")
            key = {
                "DISCOVERED": "discovered",
                "ANALYZING": "discovered",
                "QUALIFIED": "qualified",
                "PENDING_APPROVAL": "pending_approval",
                "APPROVED": "approved",
                "EXECUTING": "executing",
                "QA": "executing",
                "READY_TO_DELIVER": "executing",
                "DELIVERED": "delivered",
                "PAYMENT_PENDING": "payment_pending",
                "PAID": "paid",
                "REJECTED": "rejected",
            }.get(st)
            if key:
                counts[key] = counts.get(key, 0) + 1
        return counts

    def import_opportunity(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self._store.import_opportunity(payload or {})
        deduped = bool(row.get("_deduped"))
        if "_deduped" in row:
            row = {k: v for k, v in row.items() if k != "_deduped"}
        return {"ok": True, "opportunity": row, "deduped": deduped}

    def top(self, *, limit: int = 20) -> list[dict[str, Any]]:
        return self._store.top(limit=limit, first_money=True)

    def get(self, opportunity_id: str) -> dict[str, Any] | None:
        return self._store.get(opportunity_id)

    def reject(self, opportunity_id: str, *, note: str = "") -> dict[str, Any]:
        row = self._store.set_status(
            opportunity_id,
            "REJECTED",
            extra={"reject_note": (note or "").strip(), "updated_at": _now()},
        )
        self._store.emit(
            "opportunity_rejected",
            opportunity_id=opportunity_id,
            status="REJECTED",
            extra={"note": note},
        )
        return {"ok": True, "opportunity": row}

    def approve(self, opportunity_id: str, *, note: str = "", confirm: bool = False) -> dict[str, Any]:
        row = self._store.get(opportunity_id)
        if not row:
            return {"ok": False, "error": "not_found"}
        if row.get("status") == "REJECTED":
            return {"ok": False, "error": "already_rejected"}
        eco = row.get("economics") or {}
        preview = {
            "expected_revenue": eco.get("expected_revenue"),
            "maximum_cost": eco.get("expected_cost"),
            "toloka_cost": eco.get("toloka_cost"),
            "ai_cost": eco.get("ai_cost"),
            "other": round(
                float(eco.get("infrastructure_cost") or 0)
                + float(eco.get("estimated_internal_cost") or 0)
                + float(eco.get("platform_fee") or 0)
                + float(eco.get("risk_reserve") or 0),
                2,
            ),
            "expected_profit": eco.get("expected_profit"),
            "spend_band": eco.get("spend_band"),
            "note_ru": "Подтверждение разрешает платные execution steps в пределах maximum_cost.",
        }
        if not confirm:
            return {
                "ok": True,
                "requires_confirm": True,
                "approval_preview": preview,
                "opportunity": row,
            }

        plan = self._build_execution_plan(row)
        proposal = self._build_proposal(row, plan)
        approval = {
            "approved_at": _now(),
            "note": (note or "").strip(),
            "max_cost_eur": float(eco.get("expected_cost") or 0),
            "preview": preview,
        }
        row = self._store.set_status(
            opportunity_id,
            "APPROVED",
            extra={
                "approval": approval,
                "execution_plan": plan,
                "proposal": proposal,
            },
        )
        self._store.emit(
            "opportunity_approved",
            opportunity_id=opportunity_id,
            status="APPROVED",
            cost=float(eco.get("expected_cost") or 0),
        )
        # Enqueue dry-run style note into Farm Engine when available (no auto spend).
        farm_enqueue = self._try_farm_enqueue(row)
        return {
            "ok": True,
            "opportunity": row,
            "execution_plan": plan,
            "proposal": proposal,
            "farm_enqueue": farm_enqueue,
            "toloka": {
                "allowed": False,
                "reason_ru": "Toloka create_task только после отдельного cost estimate + approval.",
                "estimate_eur": eco.get("toloka_cost"),
            },
        }

    def _try_farm_enqueue(self, row: dict[str, Any]) -> dict[str, Any]:
        try:
            from swarm.farm_engine_v1 import FarmEngineV1

            eng = FarmEngineV1(self._memory)
            # Register as research passport note — does not create fake revenue.
            return {
                "ok": True,
                "note_ru": "Money Hunter approval recorded; paid Toloka/API still gated.",
                "opportunity_id": row.get("id"),
                "engine": "farm_engine_v1",
                "panel_mode": getattr(eng, "mode", None) or "research_dry_run",
            }
        except Exception as exc:  # noqa: BLE001 — soft link
            return {"ok": False, "error": str(exc)[:200]}

    def _build_execution_plan(self, row: dict[str, Any]) -> dict[str, Any]:
        eco = row.get("economics") or {}
        return {
            "opportunity_id": row.get("id"),
            "goal": row.get("title"),
            "deliverable_hint": row.get("category") or "WEB_RESEARCH",
            "deadline": row.get("deadline") or "",
            "budget_max_eur": eco.get("expected_cost"),
            "allowed_spend_eur": 0.0,  # raised only after Toloka/API sub-approval
            "allowed_tools": ["vector", "public_web_research", "local_files"],
            "forbidden": [
                "captcha_bypass",
                "credential_theft",
                "spam",
                "fake_engagement",
                "auto_spend",
            ],
            "human_gate": {
                "confidence_auto": 0.90,
                "confidence_optional_qa": 0.70,
                "below": "mandatory_human_review",
            },
            "steps": [
                {"id": "brief", "owner": "vector", "status": "ready"},
                {"id": "execute", "owner": "vector_workers", "status": "blocked_until_start"},
                {
                    "id": "toloka_if_needed",
                    "owner": "toloka_provider",
                    "status": "requires_cost_approval",
                    "estimate_eur": eco.get("toloka_cost"),
                },
                {"id": "qa", "owner": "qa", "status": "pending"},
                {"id": "delivery", "owner": "delivery_engine", "status": "pending"},
            ],
            "stop_when": [
                "budget_exceeded",
                "forbidden_action_requested",
                "client_illegal_request",
            ],
            "created_at": _now(),
        }

    def _build_proposal(self, row: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        eco = row.get("economics") or {}
        title = row.get("title") or "your project"
        text = (
            f"Hi — I reviewed «{title}».\n\n"
            f"Understanding: {str(row.get('description') or '')[:280]}\n\n"
            f"Plan: {plan.get('deliverable_hint')} via Virtus Core "
            f"(AI + human QA where needed).\n"
            f"Timeline: ~{eco.get('estimated_hours')} h estimated effort.\n"
            f"Price: €{eco.get('expected_revenue')} "
            f"(your stated budget band).\n\n"
            f"Capabilities: research, data verification, content QA, structured delivery.\n"
            f"Questions: preferred format (CSV/JSON/PDF)? hard deadline?\n\n"
            f"— Virtus Core / Vector\n"
            f"(NOT auto-sent — COPY only until separate submit approval)"
        )
        return {
            "text": text,
            "auto_submit": False,
            "copy_only": True,
            "created_at": _now(),
        }

    def start_execution(self, opportunity_id: str) -> dict[str, Any]:
        row = self._store.get(opportunity_id)
        if not row:
            return {"ok": False, "error": "not_found"}
        if row.get("status") != "APPROVED":
            return {"ok": False, "error": "not_approved", "status": row.get("status")}
        row = self._store.set_status(opportunity_id, "EXECUTING")
        self._store.emit("execution_started", opportunity_id=opportunity_id, status="EXECUTING")
        return {"ok": True, "opportunity": row, "execution_plan": row.get("execution_plan")}

    def create_delivery(self, opportunity_id: str, *, artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
        row = self._store.get(opportunity_id)
        if not row:
            return {"ok": False, "error": "not_found"}
        if row.get("status") not in ("APPROVED", "EXECUTING", "QA", "READY_TO_DELIVER"):
            return {"ok": False, "error": "bad_status", "status": row.get("status")}

        self._store.set_status(opportunity_id, "QA")
        self._store.emit("qa_started", opportunity_id=opportunity_id, status="QA")

        delivery_dir = self._memory / "money_hunter_delivery" / str(opportunity_id)
        delivery_dir.mkdir(parents=True, exist_ok=True)
        payload = artifacts or {
            "summary": f"Delivery package for {row.get('title')}",
            "opportunity_id": opportunity_id,
            "note": "Populate with real work results before sending to client.",
        }
        (delivery_dir / "result.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (delivery_dir / "result.csv").write_text(
            "field,value\nopportunity_id," + opportunity_id + "\n", encoding="utf-8"
        )
        (delivery_dir / "README.md").write_text(
            f"# Delivery — {row.get('title')}\n\n"
            f"Checklist:\n"
            f"- [ ] Results reviewed\n"
            f"- [ ] No PII leaked\n"
            f"- [ ] Format matches client request\n"
            f"- [ ] CEO approved send\n",
            encoding="utf-8",
        )
        # Placeholder PDF marker (no fake invoice).
        (delivery_dir / "report.pdf").write_bytes(b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n")

        checklist = {
            "reviewed": False,
            "no_pii": False,
            "format_ok": False,
            "ceo_send_approved": False,
        }
        delivery = {
            "path": str(delivery_dir),
            "files": ["result.csv", "result.json", "report.pdf", "README.md"],
            "checklist": checklist,
            "created_at": _now(),
        }
        row = self._store.set_status(
            opportunity_id,
            "READY_TO_DELIVER",
            extra={"delivery": delivery},
        )
        self._store.emit("delivery_created", opportunity_id=opportunity_id, status="READY_TO_DELIVER")
        return {"ok": True, "opportunity": row, "delivery": delivery}

    def mark_delivered(self, opportunity_id: str) -> dict[str, Any]:
        row = self._store.get(opportunity_id)
        if not row:
            return {"ok": False, "error": "not_found"}
        delivery = row.get("delivery") or {}
        checklist = delivery.get("checklist") or {}
        if not all(checklist.get(k) for k in ("reviewed", "format_ok", "ceo_send_approved")):
            return {
                "ok": False,
                "error": "checklist_incomplete",
                "checklist": checklist,
                "note_ru": "Нельзя отправлять клиенту непроверенный результат.",
            }
        row = self._store.set_status(opportunity_id, "DELIVERED")
        self._store.emit("delivery_sent", opportunity_id=opportunity_id, status="DELIVERED")
        row = self._store.set_status(opportunity_id, "PAYMENT_PENDING")
        return {"ok": True, "opportunity": row}

    def record_settlement(self, opportunity_id: str, settlement: dict[str, Any]) -> dict[str, Any]:
        """Only Hard REAL settlements may set real_revenue / PAID."""
        from swarm.finance_ledger import FinanceLedger
        from swarm.finance_reality_law import is_real_money_event

        row = self._store.get(opportunity_id)
        if not row:
            return {"ok": False, "error": "not_found"}

        event = {
            "external_payout_id": settlement.get("external_payout_id"),
            "amount": settlement.get("amount"),
            "currency": settlement.get("currency") or "EUR",
            "paid_at": settlement.get("paid_at") or _now(),
            "source_id": settlement.get("source_id") or "money_hunter_settlement",
        }
        if not is_real_money_event(event):
            return {
                "ok": False,
                "error": "not_hard_real",
                "note_ru": "Нужны external_payout_id + amount + currency + paid_at + source.",
                "potential_only": True,
            }

        # Idempotent: same payout id must not double-count.
        prev = row.get("paid_settlement") or {}
        if prev.get("external_payout_id") == event["external_payout_id"] and row.get("status") == "PAID":
            return {"ok": True, "duplicate": True, "opportunity": row}

        amount_eur = float(event["amount"] or 0)
        ledger = FinanceLedger(self._memory)
        ledger.append(
            source_id=str(event["source_id"]),
            amount=amount_eur,
            currency=str(event["currency"] or "EUR"),
            income_type="revenue",
            description=f"Money Hunter settlement {opportunity_id}",
            payout_id=str(event["external_payout_id"]),
            task_id=str(opportunity_id),
            settlement_date=str(event["paid_at"])[:10],
        )
        row = self._store.set_status(
            opportunity_id,
            "PAID",
            extra={
                "paid_settlement": event,
                "real_revenue_eur": amount_eur,
            },
        )
        self._store.emit(
            "payment_received",
            opportunity_id=opportunity_id,
            status="PAID",
            cost=0.0,
            extra={"amount": amount_eur},
        )
        self._store.emit(
            "revenue_recorded",
            opportunity_id=opportunity_id,
            status="PAID",
            extra={"amount": amount_eur, "external_payout_id": event["external_payout_id"]},
        )
        return {"ok": True, "opportunity": row, "real_revenue_eur": amount_eur}

    def reality(self) -> dict[str, Any]:
        """Strictly separated numbers — never mix potential into real."""
        real_revenue = 0.0
        paid_orders = 0
        pipeline_value = 0.0
        expected_profit = 0.0
        active = 0
        for row in self._store.list_all():
            st = str(row.get("status") or "")
            eco = row.get("economics") or {}
            if st == "PAID":
                paid_orders += 1
                real_revenue += float(row.get("real_revenue_eur") or 0)
            if st in (
                "DISCOVERED",
                "ANALYZING",
                "QUALIFIED",
                "PENDING_APPROVAL",
                "APPROVED",
                "EXECUTING",
                "QA",
                "READY_TO_DELIVER",
                "DELIVERED",
                "PAYMENT_PENDING",
            ):
                active += 1
                pipeline_value += float(eco.get("expected_revenue") or 0)
                expected_profit += float(eco.get("expected_profit") or 0)

        # Ledger REAL (may include RapidAPI etc.) — separate field.
        ledger_real = 0.0
        try:
            from swarm.finance_ledger import FinanceLedger

            snap = FinanceLedger(self._memory).summary()
            ledger_real = float(
                snap.get("real_withdrawable_eur")
                or snap.get("real_total_eur")
                or snap.get("real_eur")
                or 0
            )
        except Exception:  # noqa: BLE001
            ledger_real = 0.0

        toloka_balance = None
        toloka_spend = 0.0
        try:
            # Spend status only — never income.
            from swarm.adapter_toloka import probe_toloka_balance  # type: ignore

            bal = probe_toloka_balance()
            if isinstance(bal, dict):
                toloka_balance = bal.get("balance_usd")
        except Exception:  # noqa: BLE001
            toloka_balance = None

        return {
            "real_revenue_eur": round(real_revenue, 2),
            "real_paid_orders": paid_orders,
            "ledger_real_eur": round(ledger_real, 2),
            "pipeline_value_eur": round(pipeline_value, 2),
            "expected_profit_eur": round(expected_profit, 2),
            "toloka_balance_usd": toloka_balance,
            "toloka_spend_usd": toloka_spend,
            "active_opportunities": active,
            "layers": {
                "REAL_MONEY": "confirmed settlements only",
                "FARM_POTENTIAL": "pipeline_value + expected_profit",
                "TOLOKA_BALANCE": "spend wallet — not revenue",
                "TRAINING_SIMULATION": "never shown as REAL",
            },
        }

    def toloka_estimate(self, opportunity_id: str) -> dict[str, Any]:
        row = self._store.get(opportunity_id)
        if not row:
            return {"ok": False, "error": "not_found"}
        eco = row.get("economics") or {}
        return {
            "ok": True,
            "provider": "TolokaProvider",
            "role": "execution_spend",
            "estimate_cost_eur": eco.get("toloka_cost"),
            "create_allowed": False,
            "gate": ["COST_ESTIMATE", "CEO_APPROVAL", "CREATE_TOLOKA_TASK"],
            "note_ru": "Баланс Toloka — расход requester, не доход.",
        }
