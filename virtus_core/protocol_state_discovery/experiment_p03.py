"""
Experiment P-03 — Golem Provider Mainnet Observation

STATUS: FROZEN (2026-09-01) — not primary track.
Primary research moved to VCORE Exchangeability Engine.
Retained as lab journal only — do not extend field observation.

P-01 → taxonomy #2 (capital required before compute)
P-02 → taxonomy #3 candidate (capital-free, demand unproven)
P-03 → attempt taxonomy #4 (real work → real payout)

Key distinction (owner 2026-09-01):
  €0 CAPITAL ≠ €0 COST
  electricity · internet · hardware · gas-on-withdraw · idle time are real costs.

Phase A: observational — no artificial job, no stake, no token purchase
Phase B: settlement proof — job_id + amount + billing + Polygon TXID

No job matched ≠ theory wrong → market-demand blocker (still taxonomy #3).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from virtus_core.protocol_state_discovery.experiment_p02 import run_experiment_p02
from virtus_core.protocol_state_discovery.golem_observer import (
    GLM_POLYGON,
    run_phase_a_observation,
    run_phase_b_settlement,
)

_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME = _ROOT / ".runtime" / "experiments"
_LAST = _RUNTIME / "p03_last.json"

# Research taxonomy — four distinct outcomes Virtus must not conflate.
TAXONOMY_STATES: dict[int, dict[str, str]] = {
    1: {
        "id": "TECHNICALLY_IMPOSSIBLE",
        "label": "Невозможно технически",
        "example": "No public work path / security rejected",
    },
    2: {
        "id": "POSSIBLE_BUT_CAPITAL_REQUIRED",
        "label": "Возможно, но нужен капитал",
        "example": "P-01 Livepeer — stake before compute",
    },
    3: {
        "id": "CAPITAL_FREE_DEMAND_UNPROVEN",
        "label": "Без капитала, спрос не доказан",
        "example": "P-02 Golem provider-path — filters pass, no TX yet",
    },
    4: {
        "id": "REAL_WORK_REAL_PAYOUT",
        "label": "Реальная работа → реальная выплата",
        "example": "P-03 Phase B — job + GLM + Polygon TXID",
    },
}

# Formalized research dimensions (separate capital from cost).
RESEARCH_DIMENSIONS: tuple[str, ...] = (
    "CAPITAL_FREE",
    "COST_FREE",
    "TRANSFERABLE_ASSET",
    "REAL_PUBLIC_PROTOCOL",
    "PUBLIC_WORK",
    "VERIFIABLE_WORK",
    "DETERMINISTIC_AMOUNT",
    "GUARANTEED_DEMAND",
    "OBSERVED_DEMAND",
    "REAL_TRANSACTION",
)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _golem_dimensions(*, phase_a: dict[str, Any], phase_b: dict[str, Any]) -> dict[str, str]:
    """PASS | FAIL | UNKNOWN | NOT_YET_OBSERVED"""
    pa = phase_a.get("phase_a_status") or ""
    pb = phase_b.get("phase_b_status") or ""
    has_job = bool((phase_a.get("settlement_hints") or {}).get("job_id"))
    has_tx = bool(phase_b.get("polygon_txid"))

    return {
        "CAPITAL_FREE": "PASS",
        "COST_FREE": "UNKNOWN",
        "COST_NOTE": "€0 capital ≠ €0 cost — electricity/hardware/gas/idle not measured in P-03 snapshot",
        "TRANSFERABLE_ASSET": "PASS",
        "REAL_PUBLIC_PROTOCOL": "PASS",
        "PUBLIC_WORK": "PASS",
        "VERIFIABLE_WORK": "PASS",
        "DETERMINISTIC_AMOUNT": "FAIL",
        "GUARANTEED_DEMAND": "FAIL",
        "OBSERVED_DEMAND": (
            "PASS"
            if has_job
            else (
                "NOT_YET_OBSERVED"
                if pa
                in (
                    "OBSERVING_NO_MATCH_YET",
                    "WAITING_PROVIDER_START",
                    "PREREQUISITES_MISSING",
                    "JOB_ACTIVITY_SEEN",
                )
                else "FAIL"
            )
        ),
        "REAL_TRANSACTION": "PASS" if has_tx else "NOT_YET_OBSERVED",
    }


def _taxonomy_id(*, phase_a: dict[str, Any], phase_b: dict[str, Any]) -> int:
    pb = phase_b.get("phase_b_status") or ""
    if pb == "SETTLEMENT_TX_OBSERVED":
        return 4
    pa = phase_a.get("phase_a_status") or ""
    if pa in ("PREREQUISITES_MISSING",):
        return 3
    if pb in ("NO_JOB_NO_SETTLEMENT", "JOB_WITHOUT_BILLING", "BILLING_WITHOUT_TXID") or pa in (
        "OBSERVING_NO_MATCH_YET",
        "WAITING_PROVIDER_START",
        "JOB_ACTIVITY_SEEN",
    ):
        return 3
    return 3


def run_experiment_p03(*, include_p02_context: bool = True) -> dict[str, Any]:
    """Run P-03 Golem field observation (snapshot). Long-running watch = repeated calls."""
    phase_a = run_phase_a_observation()
    phase_b = run_phase_b_settlement(phase_a=phase_a)
    dimensions = _golem_dimensions(phase_a=phase_a, phase_b=phase_b)
    tax_id = _taxonomy_id(phase_a=phase_a, phase_b=phase_b)

    p02_ctx = None
    if include_p02_context:
        p02 = run_experiment_p02(include_p01_control=False)
        p02_ctx = {
            "best": (p02.get("best_candidate") or {}).get("protocol"),
            "p02_outcome": p02.get("experiment_outcome"),
        }

    brick_state = phase_b.get("economic_brick_state") or "INCOMPLETE_ECONOMIC_BRICK"
    if dimensions["REAL_TRANSACTION"] != "PASS":
        brick_state = "INCOMPLETE_ECONOMIC_BRICK"

    if tax_id == 4:
        outcome = "P03_TAXONOMY_4_SETTLEMENT"
        message = "P-03: наблюдена settlement TX — owner verify → REAL_EXTERNAL_ASSET."
    elif phase_a.get("phase_a_status") == "PREREQUISITES_MISSING":
        outcome = "P03_WAITING_PROVIDER_INSTALL"
        message = (
            "P-03 Phase A: provider не установлен/не запущен. Taxonomy #3 сохраняется. "
            "Следующий шаг: WSL/Linux + Golem provider mainnet — без покупки stake."
        )
    elif phase_a.get("phase_a_status") == "WAITING_PROVIDER_START":
        outcome = "P03_WAITING_DAEMON"
        message = "P-03: yagna/golemsp есть, daemon не слушает. Запустить provider → повторить observation."
    elif phase_a.get("phase_a_status") == "OBSERVING_NO_MATCH_YET":
        outcome = "P03_NO_DEMAND_YET"
        message = (
            "P-03: capital-free path жив, job match не наблюдён — market-demand blocker, не провал теории. "
            "Taxonomy #3."
        )
    elif phase_a.get("phase_a_status") == "JOB_ACTIVITY_SEEN":
        outcome = "P03_JOB_SEEN_VERIFY_SETTLEMENT"
        message = "P-03: activity seen — Phase B needs billing + Polygon TXID for CANDIDATE_REAL."
    else:
        outcome = "P03_IN_PROGRESS"
        message = "P-03 observation in progress."

    report = {
        "experiment_id": "P-03",
        "title": "Golem Provider — Mainnet Observation",
        "version": "1.0.0",
        "at": _now(),
        "protocol": "Golem Network (Yagna provider)",
        "network": "Polygon mainnet (GLM)",
        "glm_polygon_contract": GLM_POLYGON,
        "axiom": "€0 CAPITAL ≠ €0 COST — capital-free ≠ cost-free",
        "forbidden": [
            "artificial job injection",
            "token purchase for experiment",
            "stake",
            "paint REAL without TXID",
            "VCORE as liquidity",
        ],
        "phases": {
            "A": {
                "mode": "observational_only",
                "flow": "Yagna mainnet → provider configured → owner wallet → wait legitimate match",
                "result": phase_a,
            },
            "B": {
                "mode": "settlement_if_observed",
                "flow": "job_id + GLM amount + billing + Polygon TXID",
                "result": phase_b,
            },
        },
        "research_dimensions": dimensions,
        "economic_brick": {
            "state": brick_state,
            "summary": (
                "CAPITAL_FREE PASS · DETERMINISTIC_AMOUNT FAIL · GUARANTEED_DEMAND FAIL · "
                f"REAL_TRANSACTION {dimensions['REAL_TRANSACTION']}"
            ),
        },
        "taxonomy": {
            "current_id": tax_id,
            "current": TAXONOMY_STATES[tax_id],
            "all_states": TAXONOMY_STATES,
            "progression": "P-01=#2 · P-02=#3 candidate · P-03 seeks #4",
        },
        "experiment_outcome": outcome,
        "message": message,
        "p02_context": p02_ctx,
        "real_external_asset": {
            "count": 1 if phase_b.get("real_external_asset") == "REAL_EXTERNAL_ASSET_PENDING_OWNER_VERIFY" else 0,
            "txid": phase_b.get("polygon_txid"),
            "note": "Count stays 0 until owner confirms external TX + balance delta",
        },
        "next": {
            "install": "Linux/WSL: Golem provider docs → YA_PAYMENT_NETWORK_GROUP=mainnet → YA_ACCOUNT=owner",
            "observe": "Re-run P-03 snapshot periodically — journal appends to p03_observation_journal.jsonl",
            "success": "Phase B: job_id + actual GLM + billing evidence + Polygon TXID",
        },
        "agent_policy": {
            "no_job_is_not_theory_failure": True,
            "market_demand_blocker": "taxonomy #3",
            "may_end_with": "P03_NO_DEMAND_YET",
        },
    }

    _RUNTIME.mkdir(parents=True, exist_ok=True)
    (_RUNTIME / "p03_golem_mainnet_observation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _LAST.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
