"""
Economic Brick schema — single truth for Opportunity AI / Protocol State Discovery.

Statuses:
  INCOMPLETE_ECONOMIC_BRICK — missing any critical field
  CANDIDATE_REAL_BRICK      — all fields filled + frictionless; not yet paid
  REAL_EXTERNAL_ASSET       — only after confirmed external TX + balance delta
"""

from __future__ import annotations

from typing import Any

# Exact fields the owner asked Opportunity AI to fill for every candidate.
BRICK_FIELDS: tuple[str, ...] = (
    "ACTION",
    "SOURCE",
    "ASSET",
    "AMOUNT",
    "DESTINATION",
    "CAPITAL",
    "GAS",
    "REGISTRATION",
    "KYC",
    "APPLICATION",
    "DEPOSIT",
    "PURCHASE",
    "STAKE",
    "PAYOUT_RULE",
    "ON_CHAIN_PROOF",
    "TRANSFERABILITY",
)

# Must be known / concrete for CANDIDATE_REAL_BRICK
CRITICAL_KNOWN = (
    "ACTION",
    "SOURCE",
    "ASSET",
    "AMOUNT",
    "DESTINATION",
    "PAYOUT_RULE",
    "ON_CHAIN_PROOF",
    "TRANSFERABILITY",
)

# Must be False / €0 for zero-capital path
FRICTION_FALSE = (
    "REGISTRATION",
    "KYC",
    "APPLICATION",
    "DEPOSIT",
    "PURCHASE",
    "STAKE",
)


def _unk(v: Any) -> bool:
    if v is None:
        return True
    s = str(v).strip().upper()
    return s in ("", "UNKNOWN", "NONE", "НЕИЗВЕСТНО", "N/A", "—", "-", "VARIES", "SEE_ELIGIBILITY")


def _truthy_flag(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in ("1", "true", "yes", "required", "да")


def extract_brick(opp: dict[str, Any]) -> dict[str, Any]:
    """Normalize any opportunity-like dict into the owner brick schema."""
    capital = float(opp.get("capital_required") or opp.get("capital_required_eur") or opp.get("CAPITAL") or 0)
    gas = float(opp.get("gas_required") or opp.get("gas_required_eur") or opp.get("GAS") or 0)
    amount = opp.get("expectedAmount")
    if amount is None:
        amount = opp.get("expected_gross")
    if amount is None:
        amount = opp.get("AMOUNT")

    action = opp.get("ACTION") or opp.get("action") or opp.get("required_action")
    source = (
        opp.get("SOURCE")
        or opp.get("source")
        or opp.get("sourceType")
        or opp.get("source_of_funds_type")
    )
    asset = opp.get("ASSET") or opp.get("asset") or opp.get("counterAsset")
    dest = (
        opp.get("DESTINATION")
        or opp.get("destination")
        or opp.get("withdrawalPath")
        or opp.get("withdrawal_path")
    )
    payout = (
        opp.get("PAYOUT_RULE")
        or opp.get("payout_rule")
        or opp.get("reward_rule")
        or opp.get("eligibility")
    )
    proof = (
        opp.get("ON_CHAIN_PROOF")
        or opp.get("on_chain_proof")
        or opp.get("evidence")
        or opp.get("source_of_funds_evidence")
        or opp.get("url")
    )
    xfer = opp.get("TRANSFERABILITY") or opp.get("transferability")
    if xfer is None:
        # Infer poorly: only claim transferable if asset known and not VCORE-only fantasy
        if not _unk(asset) and str(asset).upper() not in ("VCORE", "REWARD_TOKEN", "PROTOCOL_REWARD"):
            xfer = "UNKNOWN_UNTIL_RECEIVED"
        else:
            xfer = "UNKNOWN"

    brick = {
        "ACTION": action if not _unk(action) else None,
        "SOURCE": source if not _unk(source) else None,
        "ASSET": asset if not _unk(asset) else None,
        "AMOUNT": amount if amount not in (None, "", 0, 0.0) else None,
        "DESTINATION": dest if not _unk(dest) else None,
        "CAPITAL": capital,
        "GAS": gas,
        "REGISTRATION": _truthy_flag(
            opp.get("REGISTRATION") if "REGISTRATION" in opp else (opp.get("registration_required") or opp.get("account_required"))
        ),
        "KYC": _truthy_flag(opp.get("KYC") if "KYC" in opp else opp.get("kyc_required")),
        "APPLICATION": _truthy_flag(
            opp.get("APPLICATION")
            if "APPLICATION" in opp
            else (
                opp.get("application_required")
                or opp.get("approval_required")
                or ("proposal" in str(opp.get("eligibility") or "").lower())
            )
        ),
        "DEPOSIT": _truthy_flag(opp.get("DEPOSIT") if "DEPOSIT" in opp else opp.get("deposit_required")),
        "PURCHASE": _truthy_flag(opp.get("PURCHASE") if "PURCHASE" in opp else opp.get("purchase_required")),
        "STAKE": _truthy_flag(opp.get("STAKE") if "STAKE" in opp else opp.get("stake_required")),
        "PAYOUT_RULE": payout if not _unk(payout) else None,
        "ON_CHAIN_PROOF": proof if not _unk(proof) and str(proof).lower() not in ("research", "hypothesis", "unknown") else None,
        "TRANSFERABILITY": xfer if not _unk(xfer) else None,
    }
    return brick


def missing_critical(brick: dict[str, Any]) -> list[str]:
    miss: list[str] = []
    for k in CRITICAL_KNOWN:
        v = brick.get(k)
        if k == "AMOUNT":
            try:
                if v is None or float(v) <= 0:
                    miss.append(k)
            except (TypeError, ValueError):
                miss.append(k)
        elif _unk(v):
            miss.append(k)
    # Evidence that is only a research label
    proof = brick.get("ON_CHAIN_PROOF")
    if proof and ("RESEARCH" in str(proof).upper() or "HYPOTHESIS" in str(proof).upper()):
        if "ON_CHAIN_PROOF" not in miss:
            miss.append("ON_CHAIN_PROOF")
    return miss


def friction_violations(brick: dict[str, Any]) -> list[str]:
    bad: list[str] = []
    if float(brick.get("CAPITAL") or 0) > 0:
        bad.append("CAPITAL")
    for k in FRICTION_FALSE:
        if brick.get(k):
            bad.append(k)
    return bad


def classify_brick(
    opp: dict[str, Any],
    *,
    confirmed_tx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    INCOMPLETE_ECONOMIC_BRICK | CANDIDATE_REAL_BRICK | REAL_EXTERNAL_ASSET
    """
    brick = extract_brick(opp)
    miss = missing_critical(brick)
    friction = friction_violations(brick)

    if confirmed_tx and confirmed_tx.get("txid") and confirmed_tx.get("confirmed"):
        return {
            "status": "REAL_EXTERNAL_ASSET",
            "brick": brick,
            "missing": [],
            "friction_violations": friction,
            "txid": confirmed_tx.get("txid"),
            "research_question_answer": "PROVEN_BY_CHAIN",
        }

    if friction:
        status = "INCOMPLETE_ECONOMIC_BRICK"
        reason = "friction_gates_failed"
    elif miss:
        status = "INCOMPLETE_ECONOMIC_BRICK"
        reason = "missing_critical_fields"
    else:
        status = "CANDIDATE_REAL_BRICK"
        reason = "schema_complete_awaiting_tx"

    return {
        "status": status,
        "reason": reason,
        "brick": brick,
        "missing": miss,
        "friction_violations": friction,
        "fields_schema": list(BRICK_FIELDS),
    }
