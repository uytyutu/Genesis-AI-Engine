"""SmartGateApproval — conditional auto-approve with CEO fallback queue."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_DEFAULT_APPROVAL_RULES: dict[str, Any] = {
    "max_risk_score": 0.1,
    "junk_micro_max_risk_score": 0.35,
    "min_expected_margin_eur": 2.0,
    "junk_micro_min_margin_eur": 0.5,
    "min_profit_margin_eur": 5.0,
    "min_domain_age_days": 365,
    "require_ssl": True,
    "ssl_revival_exception": True,
    "blacklist_keywords": ["casino", "betting", "adult", "phishing", "porn", "escort"],
    "blacklist_patterns": ["crypto_scam", "nft_mint", "pump"],
    "max_outreach_attempts": 3,
    "never_auto_approve": ["arbitrage_buy", "asset_purchase", "domain_buy", "wallet_claim"],
    "auto_approve_contexts": ["junk_micro", "outreach", "seo_revival", "bounty_report"],
    "note": "Hunter-Gatherer Smart-Gate — безопасные сделки авто, остальное CEO.",
}


@dataclass
class ApprovalDecision:
    qualified: bool
    action: str
    risk_score: float
    expected_margin_eur: float
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SmartGateApprovalService:
    """Trust thresholds — auto-execute safe deals, queue risky ones for CEO."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY

    def _rules_path(self) -> Path:
        return self._memory / "approval_rules.json"

    def load_rules(self) -> dict[str, Any]:
        path = self._rules_path()
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(_DEFAULT_APPROVAL_RULES, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return dict(_DEFAULT_APPROVAL_RULES)
        try:
            merged = dict(_DEFAULT_APPROVAL_RULES)
            merged.update(json.loads(path.read_text(encoding="utf-8")))
            return merged
        except (json.JSONDecodeError, OSError):
            return dict(_DEFAULT_APPROVAL_RULES)

    def _blacklist_hit(self, row: dict[str, Any], rules: dict[str, Any]) -> str | None:
        keywords = [str(k).lower() for k in (rules.get("blacklist_keywords") or [])]
        patterns = [str(p).lower() for p in (rules.get("blacklist_patterns") or [])]
        analysis = row.get("site_analysis") if isinstance(row.get("site_analysis"), dict) else {}
        blob = " ".join(
            [
                str(row.get("company_name") or ""),
                str(row.get("website_url") or ""),
                str(row.get("fit_reason") or ""),
                " ".join(str(i) for i in (analysis.get("issues") or [])),
                str(analysis.get("title") or ""),
            ]
        ).lower()
        for kw in keywords:
            if kw and kw in blob:
                return f"blacklist_keyword:{kw}"
        for pat in patterns:
            if pat and pat in blob:
                return f"blacklist_pattern:{pat}"
        return None

    def _estimate_domain_age_days(self, row: dict[str, Any]) -> int | None:
        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        if meta.get("domain_age_days") is not None:
            return int(meta["domain_age_days"])
        analysis = row.get("site_analysis") if isinstance(row.get("site_analysis"), dict) else {}
        text = " ".join(
            [
                str(row.get("fit_reason") or ""),
                " ".join(str(i) for i in (analysis.get("issues") or [])),
            ]
        )
        years = re.findall(r"(?:copyright|©|\(c\))\s*(?:19|20)\d{2}", text, re.I)
        if years:
            return 365 * 5
        if int(analysis.get("issue_count") or 0) >= 4:
            return 400
        return None

    def compute_risk_score(self, row: dict[str, Any], *, context: str) -> float:
        rules = self.load_rules()
        risk = 0.0
        analysis = row.get("site_analysis") if isinstance(row.get("site_analysis"), dict) else {}
        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}

        if self._blacklist_hit(row, rules):
            return 1.0

        if context in (rules.get("never_auto_approve") or []):
            return 0.95

        if not analysis.get("has_https") and rules.get("require_ssl"):
            if context in ("seo_revival", "outreach", "junk_micro") and rules.get("ssl_revival_exception"):
                risk += 0.05
            else:
                risk += 0.35

        age = self._estimate_domain_age_days(row)
        min_age = int(rules.get("min_domain_age_days") or 365)
        if context == "junk_micro":
            if age is None:
                risk += 0.05
            elif age < min_age:
                risk += 0.15
        else:
            if age is None:
                risk += 0.25
            elif age < min_age:
                risk += 0.4

        attempts = int(meta.get("outreach_attempts") or 0)
        if attempts >= int(rules.get("max_outreach_attempts") or 3):
            risk += 0.5

        profit_score = int(meta.get("profit_score") or row.get("score") or 0)
        if context != "junk_micro" and profit_score < 30:
            risk += 0.15

        return round(min(1.0, risk), 3)

    def expected_margin_eur(self, row: dict[str, Any], *, context: str) -> float:
        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        if context == "junk_micro":
            return float(meta.get("junk_micro_revenue_eur") or 0.75)
        hunter_val = float(meta.get("hunter_value_eur") or 0)
        if hunter_val > 0:
            return hunter_val
        return float(row.get("potential_value_eur") or 0)

    def evaluate(self, row: dict[str, Any], *, context: str) -> ApprovalDecision:
        rules = self.load_rules()
        reasons: list[str] = []

        bl = self._blacklist_hit(row, rules)
        if bl:
            return ApprovalDecision(
                qualified=False,
                action="pending_ceo_approval",
                risk_score=1.0,
                expected_margin_eur=self.expected_margin_eur(row, context=context),
                reasons=[bl],
            )

        if context in (rules.get("never_auto_approve") or []):
            return ApprovalDecision(
                qualified=False,
                action="pending_ceo_approval",
                risk_score=0.95,
                expected_margin_eur=self.expected_margin_eur(row, context=context),
                reasons=[f"never_auto:{context}"],
            )

        if context not in (rules.get("auto_approve_contexts") or []):
            return ApprovalDecision(
                qualified=False,
                action="pending_ceo_approval",
                risk_score=0.5,
                expected_margin_eur=self.expected_margin_eur(row, context=context),
                reasons=[f"context_not_auto:{context}"],
            )

        risk = self.compute_risk_score(row, context=context)
        margin = self.expected_margin_eur(row, context=context)
        min_margin = float(
            rules.get("junk_micro_min_margin_eur")
            if context == "junk_micro"
            else rules.get("min_profit_margin_eur") or rules.get("min_expected_margin_eur") or 2.0
        )
        max_risk = float(
            rules.get("junk_micro_max_risk_score")
            if context == "junk_micro"
            else rules.get("max_risk_score") or 0.1
        )

        if risk > max_risk:
            reasons.append(f"risk>{max_risk} ({risk})")
        if margin < min_margin:
            reasons.append(f"margin<{min_margin} ({margin})")

        qualified = not reasons
        return ApprovalDecision(
            qualified=qualified,
            action="auto_executed" if qualified else "pending_ceo_approval",
            risk_score=risk,
            expected_margin_eur=margin,
            reasons=reasons or ["trust_thresholds_pass"],
        )

    def _log_decision(self, opportunity_id: str, decision: ApprovalDecision, *, context: str) -> None:
        path = self._memory / "smart_gate_log.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "at": datetime.now(timezone.utc).isoformat(),
            "opportunity_id": opportunity_id,
            "context": context,
            **decision.to_dict(),
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def auto_execute_if_qualified(
        self,
        row: dict[str, Any],
        *,
        context: str,
        opportunity_update: Any,
    ) -> dict[str, Any]:
        """Apply auto-approve side effects when trust thresholds pass."""
        decision = self.evaluate(row, context=context)
        self._log_decision(row["id"], decision, context=context)
        meta = dict(row.get("meta") or {})
        meta["smart_gate"] = {
            **decision.to_dict(),
            "context": context,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

        if not decision.qualified:
            meta["execution_status"] = "pending_ceo_approval"
            meta["smart_gate_queue"] = "manual_review_required"
            return opportunity_update(row["id"], {"meta": meta})

        meta["execution_status"] = "auto_executed"
        meta["smart_gate_queue"] = "auto_executed"
        if context == "outreach":
            meta["outreach_status"] = "auto_approved"
        elif context == "junk_micro":
            meta["junk_smart_gate_pass"] = True
        elif context in ("seo_revival", "bounty_report"):
            meta[f"{context}_approved"] = True

        return opportunity_update(row["id"], {"meta": meta})

    def dashboard(self) -> dict[str, Any]:
        rules = self.load_rules()
        auto_n = 0
        manual_n = 0
        path = self._memory / "smart_gate_log.jsonl"
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("action") == "auto_executed":
                    auto_n += 1
                else:
                    manual_n += 1
        return {
            "max_risk_score": rules.get("max_risk_score"),
            "min_expected_margin_eur": rules.get("min_expected_margin_eur"),
            "auto_executed_count": auto_n,
            "manual_review_count": manual_n,
            "blacklist_keywords": rules.get("blacklist_keywords") or [],
            "note": "Smart-Gate: безопасные сделки авто · сомнительные → CEO Approve.",
        }
