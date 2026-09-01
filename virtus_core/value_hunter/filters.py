"""Capital / gas / source-of-funds filters (MAX_CAPITAL_EUR = 0)."""

from __future__ import annotations

from typing import Any


MAX_CAPITAL_EUR = 0.0


def apply_capital_filter(
    opp: dict[str, Any],
    *,
    max_capital_eur: float = MAX_CAPITAL_EUR,
    strict_permissionless: bool = True,
) -> dict[str, Any]:
    o = dict(opp)
    capital = float(o.get("capital_required_eur") or 0)
    gas = float(o.get("gas_required_eur") or 0)
    gas_sponsored = bool(o.get("gas_sponsored"))
    kyc = bool(o.get("kyc_required"))
    reg = bool(o.get("registration_required") or o.get("account_required"))
    application = bool(o.get("application_required"))
    approval = bool(o.get("approval_required"))
    deposit = bool(o.get("deposit_required") or o.get("stake_required") or o.get("purchase_required"))
    source = (o.get("source_of_funds_type") or "").strip()
    foreign = bool(o.get("requires_foreign_wallet"))
    forbidden = bool(o.get("forbidden") or o.get("kind") == "FORBIDDEN")

    if foreign or forbidden:
        o["status"] = "SECURITY_REJECTED"
        o["reject_reason"] = "foreign_wallet_or_forbidden"
        return o
    if not source or source.upper() in ("UNKNOWN", "NONE", ""):
        o["status"] = "NO_SOURCE_OF_FUNDS"
        o["reject_reason"] = "source_of_funds_required"
        return o
    if capital > max_capital_eur:
        o["status"] = "CAPITAL_REQUIRED"
        o["reject_reason"] = f"capital_required_eur={capital}>{max_capital_eur}"
        return o
    if gas > 0 and not gas_sponsored:
        o["status"] = "GAS_REQUIRED"
        o["reject_reason"] = "gas_without_sponsor"
        return o
    if kyc:
        o["status"] = "KYC_REQUIRED"
        o["reject_reason"] = "kyc_required"
        return o

    # VH-2 strict: no account / application / grant-style participation
    if strict_permissionless:
        if application or approval or deposit:
            o["status"] = "APPLICATION_REQUIRED" if (application or approval) else "CAPITAL_REQUIRED"
            o["reject_reason"] = "strict_no_application_or_deposit"
            return o
        if reg:
            o["status"] = "REGISTRATION_REQUIRED"
            o["reject_reason"] = "registration_required"
            return o
        elig = str(o.get("eligibility") or "").lower()
        if "proposal" in elig or "acceptance" in elig or "apply" in elig:
            o["status"] = "APPLICATION_REQUIRED"
            o["reject_reason"] = "proposal_acceptance_path"
            return o
        if source.upper() in ("GRANT", "DEVELOPER_PROGRAM") or o.get("kind") in ("DEVELOPER_PROGRAM", "GRANT"):
            o["status"] = "APPLICATION_REQUIRED"
            o["reject_reason"] = "grant_class_excluded_vh2"
            return o
    else:
        if reg and o.get("strict_no_registration"):
            o["status"] = "REGISTRATION_REQUIRED"
            o["reject_reason"] = "registration_required"
            return o

    if o.get("status") in (None, "", "DISCOVERED", "VERIFIED"):
        o["status"] = "ZERO_CAPITAL" if capital <= 0 and (gas <= 0 or gas_sponsored) else o.get("status")
    if o.get("status") == "ZERO_CAPITAL":
        o["status"] = "TESTABLE"
    return o


def economic_proof(opp: dict[str, Any]) -> dict[str, Any]:
    """SOURCE → CONDITION → ACTION → REWARD → ASSET → WITHDRAWAL."""
    chain = {
        "source": opp.get("source_of_funds_description") or opp.get("title"),
        "condition": opp.get("eligibility") or "UNKNOWN",
        "required_action": opp.get("required_action") or "UNKNOWN",
        "reward_rule": opp.get("reward_rule") or "UNKNOWN",
        "expected_asset": opp.get("asset") or "UNKNOWN",
        "withdrawal_path": opp.get("withdrawal_path") or "UNKNOWN",
    }
    unknowns = [k for k, v in chain.items() if not v or str(v).upper() == "UNKNOWN"]
    ok = len(unknowns) == 0 and bool(opp.get("source_of_funds_type"))
    return {
        "ok": ok,
        "chain": chain,
        "unknowns": unknowns,
        "status": "PASS" if ok else "ECONOMIC_PROOF_FAILED",
    }


def expected_value(opp: dict[str, Any]) -> dict[str, Any]:
    gross = opp.get("expected_gross")
    gas = float(opp.get("gas_required_eur") or 0)
    fees = float(opp.get("fees_required_eur") or 0)
    prob = opp.get("probability")
    if prob is None:
        prob_s = "UNKNOWN"
        ev = None
    else:
        try:
            p = float(prob)
            g = float(gross) if gross is not None else None
            if g is None:
                prob_s = str(p)
                ev = None
            else:
                ev = round(p * g - gas - fees, 6)
                prob_s = str(p)
        except (TypeError, ValueError):
            prob_s = "UNKNOWN"
            ev = None
    return {
        "expected_gross": gross if gross is not None else "UNKNOWN",
        "expected_gas": gas,
        "expected_fees": fees,
        "probability": prob_s,
        "expected_value": ev if ev is not None else "UNKNOWN",
        "expected_net": (
            round(float(gross) - gas - fees, 6) if gross is not None else "UNKNOWN"
        ),
    }
