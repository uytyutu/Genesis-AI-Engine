"""
REAL OPPORTUNITY VERIFICATION

Every candidate must answer WHO/WHAT/WHY/ACTION/SOURCE/AMOUNT/COST/ARRIVAL/VERIFY.
Any UNKNOWN → NOT VERIFIED. Does not invent payouts.
"""

from __future__ import annotations

from typing import Any


QUESTIONS = (
    ("who_pays", "WHO PAYS?"),
    ("what_pays", "WHAT PAYS?"),
    ("why_eligible", "WHY ARE WE ELIGIBLE?"),
    ("required_action", "WHAT ACTION IS REQUIRED?"),
    ("source_of_funds", "WHERE DOES MONEY COME FROM?"),
    ("how_much", "HOW MUCH?"),
    ("what_cost", "WHAT DOES IT COST?"),
    ("where_arrives", "WHERE DOES IT ARRIVE?"),
    ("can_verify_payout", "CAN WE VERIFY THE PAYOUT?"),
)


def _unknown(v: Any) -> bool:
    if v is None:
        return True
    s = str(v).strip()
    return s == "" or s.upper() in ("UNKNOWN", "—", "-", "N/A", "NONE")


def build_answers(opp: dict[str, Any]) -> dict[str, Any]:
    capital = float(opp.get("capital_required_eur") or 0)
    gas = float(opp.get("gas_required_eur") or 0)
    fees = float(opp.get("fees_required_eur") or 0)
    gross = opp.get("expected_gross")
    if gross is None and opp.get("expected"):
        gross = opp["expected"].get("expected_gross")
    cost = f"capital€{capital}+gas€{gas}+fees€{fees}"
    return {
        "who_pays": opp.get("who_pays")
        or opp.get("protocol")
        or opp.get("source_of_funds_description"),
        "what_pays": opp.get("what_pays") or opp.get("asset"),
        "why_eligible": opp.get("why_eligible") or opp.get("eligibility"),
        "required_action": opp.get("required_action"),
        "source_of_funds": opp.get("source_of_funds_type")
        or opp.get("source_of_funds_description"),
        "how_much": gross if gross is not None else opp.get("how_much"),
        "what_cost": opp.get("what_cost") or cost,
        "where_arrives": opp.get("where_arrives") or opp.get("withdrawal_path"),
        "can_verify_payout": opp.get("can_verify_payout")
        or (
            "yes_on_chain_tx"
            if opp.get("source_of_funds_evidence") or opp.get("url")
            else None
        ),
    }


def verify_real_opportunity(opp: dict[str, Any]) -> dict[str, Any]:
    answers = build_answers(opp)
    unknown_keys = [k for k, v in answers.items() if _unknown(v)]
    # Forbidden / exit converters never get VERIFIED as income sources
    if opp.get("forbidden") or opp.get("requires_foreign_wallet") or opp.get("kind") == "FORBIDDEN":
        return {
            "status": "NOT VERIFIED",
            "reason": "security_rejected",
            "answers": answers,
            "unknowns": unknown_keys,
            "questions": [{"id": a, "label": b, "answer": answers.get(a)} for a, b in QUESTIONS],
        }
    if opp.get("status") == "EXIT_ONLY" or opp.get("kind") == "EXIT_CONVERTER":
        return {
            "status": "NOT VERIFIED",
            "reason": "exit_converter_not_source",
            "answers": answers,
            "unknowns": unknown_keys + (["source_role"] if "source_role" not in unknown_keys else []),
            "questions": [{"id": a, "label": b, "answer": answers.get(a)} for a, b in QUESTIONS],
        }
    if unknown_keys:
        return {
            "status": "NOT VERIFIED",
            "reason": f"unknown={unknown_keys}",
            "answers": answers,
            "unknowns": unknown_keys,
            "questions": [{"id": a, "label": b, "answer": answers.get(a)} for a, b in QUESTIONS],
        }
    return {
        "status": "VERIFIED",
        "reason": "all_nine_answered",
        "answers": answers,
        "unknowns": [],
        "questions": [{"id": a, "label": b, "answer": answers.get(a)} for a, b in QUESTIONS],
    }
