"""
STRICT_ZERO_CAPITAL + permissionless filter for Counter-Liquidity / VH-2.

Rejects grants, applications, accounts, KYC, deposits, stake, purchase,
manual participation. Requires automatic_payout when claiming rewards.
"""

from __future__ import annotations

from typing import Any

OWN_CAPITAL_EUR = 0.0

STRICT_DEFAULTS = {
    "ownCapitalRequired": 0.0,
    "registrationRequired": False,
    "accountRequired": False,
    "kycRequired": False,
    "applicationRequired": False,
    "approvalRequired": False,
    "depositRequired": False,
    "stakeRequired": False,
    "purchaseRequired": False,
    "manualParticipation": False,
    "automaticPayoutRequired": True,
}


def apply_strict_permissionless(opp: dict[str, Any]) -> dict[str, Any]:
    o = dict(opp)
    capital = float(o.get("capital_required") or o.get("capital_required_eur") or 0)
    gas = float(o.get("gas_required") or o.get("gas_required_eur") or 0)
    sponsor = bool(o.get("sponsor") or o.get("gas_sponsored") or o.get("sponsorProvided"))

    checks = [
        ("registrationRequired", "REGISTRATION_REQUIRED", o.get("registration_required") or o.get("registrationRequired")),
        ("accountRequired", "ACCOUNT_REQUIRED", o.get("account_required") or o.get("accountRequired")),
        ("kycRequired", "KYC_REQUIRED", o.get("kyc_required") or o.get("kycRequired")),
        ("applicationRequired", "APPLICATION_REQUIRED", o.get("application_required") or o.get("applicationRequired")),
        ("approvalRequired", "GOVERNANCE_REQUIRED", o.get("approval_required") or o.get("approvalRequired") or o.get("governance_required")),
        ("depositRequired", "CAPITAL_REQUIRED", o.get("deposit_required") or o.get("depositRequired")),
        ("stakeRequired", "CAPITAL_REQUIRED", o.get("stake_required") or o.get("stakeRequired")),
        ("purchaseRequired", "CAPITAL_REQUIRED", o.get("purchase_required") or o.get("purchaseRequired")),
        ("manualParticipation", "APPLICATION_REQUIRED", o.get("manual_participation") or o.get("manualParticipation")),
    ]
    for _name, status, flag in checks:
        if flag:
            o["status"] = status
            o["reject_reason"] = f"strict_{_name}"
            o["strict_pass"] = False
            return o

    if capital > OWN_CAPITAL_EUR:
        o["status"] = "CAPITAL_REQUIRED"
        o["reject_reason"] = f"own_capital={capital}"
        o["strict_pass"] = False
        return o

    if gas > 0 and not sponsor:
        o["status"] = "GAS_REQUIRED"
        o["reject_reason"] = "gas_without_sponsor"
        o["strict_pass"] = False
        return o

    source = (o.get("source") or o.get("sourceType") or o.get("source_of_funds_type") or "").strip()
    if not source or source.upper() in ("UNKNOWN", "NONE", ""):
        o["status"] = "NO_SOURCE"
        o["reject_reason"] = "source_unknown"
        o["strict_pass"] = False
        return o

    # Grants / bounty applications are out of VH-2 primary search
    kind = (o.get("kind") or o.get("category") or source or "").upper()
    if any(x in kind for x in ("GRANT", "BOUNTY", "AIRDROP_CAMPAIGN", "REFERRAL")):
        if o.get("application_required") is not False and (
            o.get("application_required")
            or o.get("account_required")
            or o.get("manualParticipation")
            or "proposal" in str(o.get("eligibility") or "").lower()
            or "acceptance" in str(o.get("eligibility") or "").lower()
        ):
            o["status"] = "APPLICATION_REQUIRED"
            o["reject_reason"] = "grant_or_application_class"
            o["strict_pass"] = False
            return o

    auto = o.get("automatic_payout")
    if auto is None:
        auto = o.get("automaticPayout")
    if o.get("automaticPayoutRequired", True) and auto is False:
        o["status"] = "APPLICATION_REQUIRED"
        o["reject_reason"] = "automatic_payout_required"
        o["strict_pass"] = False
        return o

    if o.get("forbidden") or o.get("requires_foreign_wallet"):
        o["status"] = "SECURITY_REJECTED"
        o["reject_reason"] = "security"
        o["strict_pass"] = False
        return o

    o["strict_pass"] = True
    if o.get("status") in (None, "", "DISCOVERED", "HYPOTHESIS"):
        o["status"] = "ZERO_CAPITAL"
    return o


def implied_vs_executable(opp: dict[str, Any]) -> dict[str, Any]:
    implied = opp.get("implied_price")
    executable = opp.get("executable_depth") or opp.get("max_executable") or opp.get("executable_price")
    return {
        "implied_price": implied if implied is not None else "UNKNOWN",
        "executable_price": executable if executable is not None else "UNKNOWN",
        "implied_ne_executable": True,
        "note": "IMPLIED ≠ EXECUTABLE — never show MODEL as available liquidity",
    }
