"""Adaptive Outreach Intelligence — weekly review, per-country scale/protect.

Does NOT auto-send mail. Only adjusts daily_cap overrides + send interval.
CEO Approve remains the send gate.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.integration.outreach_market_config import (
    get_market,
    list_markets,
    market_daily_cap as base_market_daily_cap,
)

_CONFIG_PATH = Path(__file__).resolve().parent / "outreach_adaptive.json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _load_config() -> dict[str, Any]:
    try:
        data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {"enabled": False}


class OutreachAdaptiveService:
    def __init__(self, memory_dir: Path | None) -> None:
        self._memory = memory_dir

    def _state_path(self) -> Path | None:
        if not self._memory:
            return None
        return Path(self._memory) / "outreach_adaptive_state.json"

    def _load_state(self) -> dict[str, Any]:
        path = self._state_path()
        empty = {
            "cap_overrides": {},
            "paused_markets": {},
            "zero_order_weeks": {},
            "interval_sec": None,
            "last_review_at": None,
            "next_review_at": None,
            "history": [],
            "snapshots": [],
            "last_decisions": [],
        }
        if not path or not path.is_file():
            return empty
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return empty
        if not isinstance(data, dict):
            return empty
        for key, val in empty.items():
            data.setdefault(key, val)
        return data

    def _save_state(self, state: dict[str, Any]) -> None:
        path = self._state_path()
        if not path:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def effective_daily_cap(self, code: str) -> int:
        cfg = _load_config()
        scaling = cfg.get("scaling") or {}
        lo = int(scaling.get("min_daily_cap") or 5)
        hi = int(scaling.get("max_daily_cap") or 100)
        state = self._load_state()
        paused = state.get("paused_markets") or {}
        if paused.get(str(code).upper()):
            return 0
        overrides = state.get("cap_overrides") or {}
        if str(code).upper() in overrides:
            try:
                return max(lo, min(hi, int(overrides[str(code).upper()])))
            except (TypeError, ValueError):
                pass
        return max(lo, min(hi, base_market_daily_cap(code)))

    def effective_interval_sec(self) -> int:
        cfg = _load_config()
        interval_cfg = cfg.get("interval") or {}
        lo = int(interval_cfg.get("min_sec") or 60)
        hi = int(interval_cfg.get("max_sec") or 600)
        state = self._load_state()
        if state.get("interval_sec") is not None:
            try:
                return max(lo, min(hi, int(state["interval_sec"])))
            except (TypeError, ValueError):
                pass
        from app.integration.outreach_send_quota import outreach_global_daily_cap

        # Pace against the shared mailbox ceiling, not sum of soft country shares.
        total_cap = outreach_global_daily_cap()
        total_cap = max(1, total_cap)
        base = int(36000 / total_cap)
        return max(lo, min(hi, base))

    def compute_interval_for_cap_total(self, total_cap: int) -> int:
        cfg = _load_config()
        interval_cfg = cfg.get("interval") or {}
        lo = int(interval_cfg.get("min_sec") or 60)
        hi = int(interval_cfg.get("max_sec") or 600)
        jitter = float(interval_cfg.get("jitter_pct") or 20) / 100.0
        total_cap = max(1, int(total_cap))
        base = int(36000 / total_cap)
        base = max(lo, min(hi, base))
        delta = int(base * jitter)
        if delta <= 0:
            return base
        return max(lo, min(hi, base + random.randint(-delta, delta)))

    def _market_code(self, row: dict[str, Any]) -> str | None:
        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        raw = meta.get("market") or row.get("market") or meta.get("country_code")
        if not raw:
            return None
        code = str(raw).strip().upper()
        if code == "UK":
            code = "GB"
        return code if get_market(code) else code

    def collect_market_metrics(self, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Aggregate available CRM signals per market (bounce/spam if present in meta)."""
        out: dict[str, dict[str, Any]] = {}
        for m in list_markets(enabled_only=True):
            code = str(m["code"]).upper()
            out[code] = {
                "sent": 0,
                "delivered": 0,
                "bounces": 0,
                "spam_complaints": 0,
                "replies": 0,
                "positive_replies": 0,
                "meetings": 0,
                "orders": 0,
                "revenue_eur": 0.0,
                "has_delivery_data": False,
                "has_spam_data": False,
            }

        for row in rows:
            code = self._market_code(row)
            if not code or code not in out:
                continue
            bucket = out[code]
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            outreach = str(row.get("outreach_status") or "")
            status = str(row.get("status") or "")

            if outreach in ("sent", "replied") or status in (
                "contacted",
                "replied",
                "won",
                "lost",
                "negotiation",
            ):
                bucket["sent"] += 1

            if meta.get("email_bounced") or outreach == "bounced":
                bucket["bounces"] += 1
                bucket["has_delivery_data"] = True
            if meta.get("spam_complaint"):
                bucket["spam_complaints"] += 1
                bucket["has_spam_data"] = True
            if meta.get("email_delivered"):
                bucket["delivered"] += 1
                bucket["has_delivery_data"] = True

            replied = status in ("replied", "qualified", "negotiation") or outreach == "replied"
            for ev in row.get("interactions") or []:
                if not isinstance(ev, dict):
                    continue
                ev_name = str(ev.get("event") or "")
                if ev_name in ("replied", "reply", "positive_reply"):
                    replied = True
                if ev_name in ("positive_reply", "meeting_booked", "call_booked"):
                    bucket["positive_replies"] += 1
                if ev_name in ("meeting_booked", "call_booked", "meeting"):
                    bucket["meetings"] += 1
            if replied:
                bucket["replies"] += 1

            if status == "won" or float(row.get("revenue_eur") or 0) > 0:
                bucket["orders"] += 1
                bucket["revenue_eur"] += float(row.get("revenue_eur") or row.get("potential_value_eur") or 0)

        for code, bucket in out.items():
            sent = max(0, int(bucket["sent"]))
            if sent and not bucket["has_delivery_data"]:
                # Without ESP webhooks assume delivered = sent - known bounces
                bucket["delivered"] = max(0, sent - int(bucket["bounces"]))
            bucket["delivery_rate_pct"] = (
                round(100.0 * bucket["delivered"] / sent, 2) if sent else None
            )
            bucket["bounce_rate_pct"] = (
                round(100.0 * bucket["bounces"] / sent, 2) if sent else None
            )
            bucket["spam_rate_pct"] = (
                round(100.0 * bucket["spam_complaints"] / sent, 2) if sent else None
            )
            bucket["reply_rate_pct"] = (
                round(100.0 * bucket["replies"] / sent, 2) if sent else None
            )
        return out

    def health_score(self, metrics: dict[str, Any], cfg: dict[str, Any] | None = None) -> dict[str, Any]:
        cfg = cfg or _load_config()
        thr = cfg.get("thresholds") or {}
        weights = cfg.get("weights") or {}
        sent = int(metrics.get("sent") or 0)
        if sent <= 0:
            return {
                "score": 50,
                "label": "Insufficient",
                "reasons": ["no_sends_yet"],
                "can_scale_up": False,
            }

        score = 50.0
        reasons: list[str] = []
        reply_rate = metrics.get("reply_rate_pct")
        if reply_rate is not None:
            score += min(35, (float(reply_rate) / 5.0) * float(weights.get("reply_rate") or 35) / 7)
            if float(reply_rate) < float(thr.get("reply_rate_min_pct_for_scale") or 2):
                reasons.append("reply_rate_low")

        orders = int(metrics.get("orders") or 0)
        score += min(25, orders * 8)
        revenue = float(metrics.get("revenue_eur") or 0)
        if revenue > 0:
            score += min(15, revenue / 100.0)

        bounce = metrics.get("bounce_rate_pct")
        if bounce is not None and metrics.get("has_delivery_data"):
            max_b = float(thr.get("bounce_rate_max_pct") or 3)
            if float(bounce) > max_b:
                score -= float(weights.get("bounce_penalty") or 20)
                reasons.append("bounce_above_threshold")
        spam = metrics.get("spam_rate_pct")
        if spam is not None and metrics.get("has_spam_data"):
            max_s = float(thr.get("spam_complaint_max_pct") or 0.1)
            if float(spam) > max_s:
                score -= float(weights.get("spam_penalty") or 25)
                reasons.append("spam_above_threshold")

        score = max(0, min(100, round(score)))
        excellent = int(thr.get("excellent_min_score") or 75)
        warning = int(thr.get("warning_min_score") or 45)
        if score >= excellent:
            label = "Excellent"
        elif score >= warning:
            label = "Warning"
        else:
            label = "Poor"

        min_sent = int((cfg.get("review") or {}).get("min_sent_for_scale_up") or 15)
        scaling = cfg.get("scaling") or {}
        require_rev = bool(scaling.get("require_revenue_for_scale_up", True))
        min_replies_hold = int(scaling.get("min_replies_without_revenue_hold") or 3)
        replies = int(metrics.get("replies") or 0)

        if require_rev and replies >= min_replies_hold and revenue <= 0 and orders <= 0 and sent >= min_sent:
            reasons.append("replies_without_revenue")
            can_scale_up = False
        else:
            can_scale_up = (
                label == "Excellent"
                and sent >= min_sent
                and "bounce_above_threshold" not in reasons
                and "spam_above_threshold" not in reasons
                and "reply_rate_low" not in reasons
            )
            if require_rev and can_scale_up and revenue <= 0 and orders <= 0:
                can_scale_up = False
                reasons.append("no_revenue_hold")

        can_scale_down = label == "Poor" or "bounce_above_threshold" in reasons or "spam_above_threshold" in reasons
        return {
            "score": score,
            "label": label,
            "reasons": reasons,
            "can_scale_up": can_scale_up,
            "can_scale_down": can_scale_down,
        }

    def review_due(self) -> bool:
        cfg = _load_config()
        if not cfg.get("enabled", True):
            return False
        state = self._load_state()
        last = state.get("last_review_at")
        min_days = int((cfg.get("review") or {}).get("min_days_between") or 7)
        if not last:
            return True
        try:
            last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return True
        return _utc_now() - last_dt >= timedelta(days=min_days)

    def run_weekly_review(
        self,
        rows: list[dict[str, Any]],
        *,
        force: bool = False,
        apply: bool | None = None,
    ) -> dict[str, Any]:
        cfg = _load_config()
        if not cfg.get("enabled", True):
            return {"ok": False, "reason": "adaptive_disabled"}
        if not force and not self.review_due():
            state = self._load_state()
            return {
                "ok": True,
                "skipped": True,
                "reason": "not_due",
                "next_review_at": state.get("next_review_at"),
                "last_review_at": state.get("last_review_at"),
            }

        auto_apply = cfg.get("auto_apply", True) if apply is None else bool(apply)
        scaling = cfg.get("scaling") or {}
        step_up = int(scaling.get("step_up") or 20)
        step_down = int(scaling.get("step_down") or 20)
        lo = int(scaling.get("min_daily_cap") or 5)
        hi = int(scaling.get("max_daily_cap") or 100)
        pause_weeks = int(scaling.get("auto_pause_weeks_without_orders") or 3)
        redistribute = bool(scaling.get("redistribute_on_pause", True))
        from app.integration.outreach_send_quota import outreach_global_daily_cap
        from app.integration.outreach_market_config import shared_global_mode

        gcap = outreach_global_daily_cap()
        shared = shared_global_mode()

        metrics_by = self.collect_market_metrics(rows)
        state = self._load_state()
        overrides = dict(state.get("cap_overrides") or {})
        paused = dict(state.get("paused_markets") or {})
        zero_weeks = dict(state.get("zero_order_weeks") or {})
        decisions: list[dict[str, Any]] = []
        paused_now: list[str] = []

        for m in list_markets(enabled_only=True):
            code = str(m["code"]).upper()
            metrics = metrics_by.get(code) or {}
            health = self.health_score(metrics, cfg)
            current = self.effective_daily_cap(code)
            decision = "hold"
            new_cap = current
            reason = "stable"
            orders = int(metrics.get("orders") or 0)
            revenue = float(metrics.get("revenue_eur") or 0)
            sent = int(metrics.get("sent") or 0)

            # Auto-pause: N weeks of activity with 0 deals → pause market
            if sent > 0 and orders <= 0 and revenue <= 0:
                zero_weeks[code] = int(zero_weeks.get(code) or 0) + 1
            else:
                zero_weeks[code] = 0
            if pause_weeks > 0 and int(zero_weeks.get(code) or 0) >= pause_weeks:
                paused[code] = {
                    "at": _utc_now().isoformat(),
                    "weeks": zero_weeks[code],
                    "reason": "zero_orders",
                }
                decision = "pause"
                new_cap = 0
                reason = f"auto_pause:{zero_weeks[code]}w_zero_orders"
                paused_now.append(code)
            elif paused.get(code) and (orders > 0 or revenue > 0):
                paused.pop(code, None)
                reason = "resume_after_revenue"

            if decision != "pause":
                if health.get("can_scale_up"):
                    new_cap = min(hi, current + step_up)
                    if new_cap > current:
                        decision = "scale_up"
                        reason = f"health={health['label']} score={health['score']} revenue={revenue}"
                elif health.get("can_scale_down"):
                    new_cap = max(lo, current - step_down)
                    if new_cap < current:
                        decision = "scale_down"
                        reason = ",".join(health.get("reasons") or ["poor_health"])
                elif "replies_without_revenue" in (health.get("reasons") or []) or "no_revenue_hold" in (
                    health.get("reasons") or []
                ):
                    decision = "hold"
                    reason = "profit_hold:replies_without_revenue"

            if auto_apply and decision in ("scale_up", "scale_down", "pause"):
                overrides[code] = new_cap
            elif auto_apply and decision == "hold" and code not in overrides:
                overrides[code] = current

            decisions.append(
                {
                    "code": code,
                    "flag": m.get("flag") or "",
                    "name_ru": m.get("name_ru") or code,
                    "health": health,
                    "metrics": metrics,
                    "decision": decision,
                    "from_cap": current,
                    "to_cap": new_cap if auto_apply or decision == "hold" else current,
                    "recommended_cap": new_cap,
                    "reason": reason,
                    "applied": bool(auto_apply and decision != "hold"),
                    "paused": bool(paused.get(code)),
                }
            )

        # Shared mailbox: renormalize soft budgets so they sum ≈ global_cap
        # and shift freed pause budget toward profitable markets.
        if auto_apply and shared:
            active = [d for d in decisions if not paused.get(d["code"])]
            if redistribute and paused_now:
                freed = sum(int(overrides.get(c, 0) or 0) for c in paused_now)
                for c in paused_now:
                    overrides[c] = 0
                profit_ranked = sorted(
                    active,
                    key=lambda d: (
                        float((d["metrics"] or {}).get("revenue_eur") or 0),
                        int((d["metrics"] or {}).get("orders") or 0),
                        int((d["health"] or {}).get("score") or 0),
                    ),
                    reverse=True,
                )
                i = 0
                while freed > 0 and profit_ranked:
                    code = profit_ranked[i % len(profit_ranked)]["code"]
                    cur = int(overrides.get(code, self.effective_daily_cap(code)) or 0)
                    overrides[code] = min(hi, cur + 1)
                    freed -= 1
                    i += 1
            # Cap sum of soft shares to global ceiling (weights, not hard fills)
            active_codes = [d["code"] for d in decisions if not paused.get(d["code"])]
            soft_sum = sum(int(overrides.get(c, lo) or 0) for c in active_codes) or 1
            if soft_sum > gcap and active_codes:
                scaled = {}
                acc = 0
                for idx, c in enumerate(active_codes):
                    if idx == len(active_codes) - 1:
                        scaled[c] = max(lo, gcap - acc)
                    else:
                        v = max(lo, int(round(int(overrides.get(c, lo) or 0) * gcap / soft_sum)))
                        scaled[c] = v
                        acc += v
                overrides.update(scaled)
            for d in decisions:
                if d["code"] in overrides:
                    d["to_cap"] = overrides[d["code"]]
                    d["recommended_cap"] = overrides[d["code"]]

        total_after = sum(
            int(overrides.get(str(m["code"]).upper(), self.effective_daily_cap(str(m["code"]))))
            if auto_apply
            else self.effective_daily_cap(str(m["code"]))
            for m in list_markets(enabled_only=True)
        )
        if auto_apply:
            state["cap_overrides"] = overrides
            state["paused_markets"] = paused
            state["zero_order_weeks"] = zero_weeks
        # Interval always paced to shared global mailbox ceiling
        new_interval = self.compute_interval_for_cap_total(gcap if shared else max(1, min(gcap, total_after)))
        if auto_apply:
            if any(d["decision"] == "scale_down" for d in decisions):
                new_interval = min(
                    int((cfg.get("interval") or {}).get("max_sec") or 600),
                    int(new_interval * 1.25),
                )
            state["interval_sec"] = new_interval

        now = _utc_now()
        min_days = int((cfg.get("review") or {}).get("min_days_between") or 7)
        state["last_review_at"] = now.isoformat()
        state["next_review_at"] = (now + timedelta(days=min_days)).isoformat()
        state["last_decisions"] = decisions
        history = list(state.get("history") or [])
        history.append(
            {
                "at": now.isoformat(),
                "auto_apply": auto_apply,
                "interval_sec": state.get("interval_sec"),
                "shared_global": shared,
                "global_cap": gcap,
                "decisions": [
                    {
                        "code": d["code"],
                        "decision": d["decision"],
                        "from_cap": d["from_cap"],
                        "to_cap": d["to_cap"],
                        "reason": d["reason"],
                        "health": d["health"].get("label"),
                        "score": d["health"].get("score"),
                    }
                    for d in decisions
                ],
            }
        )
        state["history"] = history[-52:]
        snap = {
            "day": now.strftime("%Y-%m-%d"),
            "at": now.isoformat(),
            "global_cap": gcap,
            "interval_sec": state.get("interval_sec"),
            "markets": {
                d["code"]: {
                    "cap": d["to_cap"],
                    "sent": d["metrics"].get("sent"),
                    "reply_rate_pct": d["metrics"].get("reply_rate_pct"),
                    "bounce_rate_pct": d["metrics"].get("bounce_rate_pct"),
                    "orders": d["metrics"].get("orders"),
                    "revenue_eur": d["metrics"].get("revenue_eur"),
                    "health_score": d["health"].get("score"),
                    "paused": d.get("paused"),
                }
                for d in decisions
            },
        }
        snapshots = list(state.get("snapshots") or [])
        snapshots.append(snap)
        state["snapshots"] = snapshots[-120:]
        self._save_state(state)

        return {
            "ok": True,
            "skipped": False,
            "auto_apply": auto_apply,
            "shared_global": shared,
            "global_cap": gcap,
            "reviewed_at": state["last_review_at"],
            "next_review_at": state["next_review_at"],
            "interval_sec": state.get("interval_sec"),
            "decisions": decisions,
            "paused_markets": list(paused.keys()),
            "note_ru": cfg.get("note_ru") or "",
        }

    def dashboard(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        cfg = _load_config()
        state = self._load_state()
        metrics_by = self.collect_market_metrics(rows)
        roi_cfg = cfg.get("roi") or {}
        cost_per = float(roi_cfg.get("cost_per_email_eur") or 0.05)
        from app.integration.outreach_send_quota import outreach_global_daily_cap
        from app.integration.outreach_market_config import shared_global_mode

        paused = state.get("paused_markets") or {}
        countries = []
        roi_table = []
        for m in list_markets(enabled_only=True):
            code = str(m["code"]).upper()
            metrics = metrics_by.get(code) or {}
            health = self.health_score(metrics, cfg)
            sent = int(metrics.get("sent") or 0)
            revenue = float(metrics.get("revenue_eur") or 0)
            orders = int(metrics.get("orders") or 0)
            spent = round(sent * cost_per, 2)
            roi = None
            if spent > 0:
                roi = round((revenue - spent) / spent, 2)
            is_paused = bool(paused.get(code))
            countries.append(
                {
                    "code": code,
                    "flag": m.get("flag") or "",
                    "name_ru": m.get("name_ru") or code,
                    "current_cap": self.effective_daily_cap(code),
                    "base_cap": base_market_daily_cap(code),
                    "health": health,
                    "metrics": metrics,
                    "paused": is_paused,
                    "spent_eur": spent,
                    "roi": roi,
                    "scaling_status": (
                        "paused"
                        if is_paused
                        else "ready_up"
                        if health.get("can_scale_up")
                        else "protect"
                        if health.get("can_scale_down")
                        else "hold"
                    ),
                    "recommended_cap": (
                        0
                        if is_paused
                        else min(
                            int((cfg.get("scaling") or {}).get("max_daily_cap") or 100),
                            self.effective_daily_cap(code)
                            + int((cfg.get("scaling") or {}).get("step_up") or 20),
                        )
                        if health.get("can_scale_up")
                        else max(
                            int((cfg.get("scaling") or {}).get("min_daily_cap") or 5),
                            self.effective_daily_cap(code)
                            - int((cfg.get("scaling") or {}).get("step_down") or 20),
                        )
                        if health.get("can_scale_down")
                        else self.effective_daily_cap(code)
                    ),
                }
            )
            roi_table.append(
                {
                    "code": code,
                    "flag": m.get("flag") or "",
                    "name_ru": m.get("name_ru") or code,
                    "spent_eur": spent,
                    "orders": orders,
                    "revenue_eur": revenue,
                    "roi": roi,
                    "paused": is_paused,
                }
            )

        overall = 0
        if countries:
            overall = round(sum(int(c["health"]["score"]) for c in countries) / len(countries))

        return {
            "ok": True,
            "enabled": bool(cfg.get("enabled", True)),
            "auto_apply": bool(cfg.get("auto_apply", True)),
            "shared_global": shared_global_mode(),
            "global_daily_cap": outreach_global_daily_cap(),
            "note_ru": cfg.get("note_ru") or "",
            "current_health": overall,
            "current_health_label": (
                "Excellent" if overall >= 75 else "Warning" if overall >= 45 else "Poor"
            ),
            "scaling_status": "review_due" if self.review_due() else "idle",
            "next_review_at": state.get("next_review_at"),
            "last_review_at": state.get("last_review_at"),
            "interval_sec": self.effective_interval_sec(),
            "countries": countries,
            "roi_table": roi_table,
            "roi_note_ru": roi_cfg.get("note_ru") or "",
            "paused_markets": list(paused.keys()),
            "last_decisions": state.get("last_decisions") or [],
            "history": state.get("history") or [],
            "graphs": self._graphs_from_snapshots(state.get("snapshots") or []),
            "config": {
                "step_up": (cfg.get("scaling") or {}).get("step_up"),
                "step_down": (cfg.get("scaling") or {}).get("step_down"),
                "max_daily_cap": (cfg.get("scaling") or {}).get("max_daily_cap"),
                "require_revenue_for_scale_up": (cfg.get("scaling") or {}).get(
                    "require_revenue_for_scale_up"
                ),
                "auto_pause_weeks_without_orders": (cfg.get("scaling") or {}).get(
                    "auto_pause_weeks_without_orders"
                ),
                "min_interval_sec": (cfg.get("interval") or {}).get("min_sec"),
                "max_interval_sec": (cfg.get("interval") or {}).get("max_sec"),
                "thresholds": cfg.get("thresholds") or {},
            },
        }

    def _graphs_from_snapshots(self, snapshots: list[dict[str, Any]]) -> dict[str, list]:
        days = []
        daily_emails = []
        reply_rates = []
        bounce_rates = []
        orders = []
        revenue = []
        health = []
        for snap in snapshots[-60:]:
            days.append(snap.get("day"))
            markets = snap.get("markets") or {}
            if not isinstance(markets, dict):
                continue
            sent = sum(int((v or {}).get("sent") or 0) for v in markets.values())
            daily_emails.append(sent)
            rr = [float(v["reply_rate_pct"]) for v in markets.values() if v.get("reply_rate_pct") is not None]
            br = [float(v["bounce_rate_pct"]) for v in markets.values() if v.get("bounce_rate_pct") is not None]
            reply_rates.append(round(sum(rr) / len(rr), 2) if rr else None)
            bounce_rates.append(round(sum(br) / len(br), 2) if br else None)
            orders.append(sum(int((v or {}).get("orders") or 0) for v in markets.values()))
            revenue.append(round(sum(float((v or {}).get("revenue_eur") or 0) for v in markets.values()), 2))
            hs = [int(v["health_score"]) for v in markets.values() if v.get("health_score") is not None]
            health.append(round(sum(hs) / len(hs)) if hs else None)
        return {
            "days": days,
            "daily_emails": daily_emails,
            "reply_rate": reply_rates,
            "bounce_rate": bounce_rates,
            "orders": orders,
            "revenue": revenue,
            "health_score": health,
            "note_ru": "Графики наполняются после weekly review / снимков. Bounce/spam точны после ESP webhooks.",
        }


def bind_adaptive_caps(memory_dir: Path | None) -> None:
    """Monkeypatch market_daily_cap resolution via adaptive overrides — called from quota."""
    # Used indirectly: OutreachAdaptiveService.effective_daily_cap
    _ = memory_dir
