"""
AI Jury — second opinion only for low-confidence, controversial turns.

Not every answer. Invoked when Genesis Director is unsure after calibration passed.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_JURY_ORDER = ("gemini", "openrouter", "groq")
_DEBATE_HINT = re.compile(
    r"поспор|плоск|земл|политик|религи|миф|заговор|прав или нет|соглас",
    re.I,
)


@dataclass(frozen=True)
class JuryVerdict:
    invoked: bool
    juror_id: str = ""
    agrees: bool = True
    concern: str = ""
    nuance: str = ""
    alternate_view: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "invoked": self.invoked,
            "juror_id": self.juror_id,
            "agrees": self.agrees,
            "concern": self.concern,
            "alternate_view": self.alternate_view,
        }


def jury_enabled() -> bool:
    return os.getenv("GENESIS_AI_JURY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def should_invoke_jury(
    *,
    confidence: float,
    chosen_employee: str,
    cloud_llm_used: bool,
    user_message: str,
    calibration_passed: bool,
) -> bool:
    if not jury_enabled() or not cloud_llm_used:
        return False
    if chosen_employee in ("genesis-local", "") or not calibration_passed:
        return False
    if confidence < 0.55:
        return True
    if _DEBATE_HINT.search(user_message or ""):
        return True
    return False


def _pick_juror(registry: dict[str, Any], chosen: str) -> Any | None:
    for jid in _JURY_ORDER:
        if jid == chosen:
            continue
        provider = registry.get(jid)
        if provider and provider.available():
            return provider
    return None


def _parse_jury_json(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    agrees = "true" in text.lower() and "false" not in text.lower()
    return {"agrees": agrees, "concern": "", "suggested_fix": None}


def invoke_jury(
    *,
    registry: dict[str, Any],
    chosen_employee: str,
    user_message: str,
    draft_answer: str,
) -> JuryVerdict:
    juror = _pick_juror(registry, chosen_employee)
    if juror is None:
        return JuryVerdict(invoked=False)

    system = (
        "Internal Genesis quality reviewer. Reply ONLY compact JSON:\n"
        '{"agrees":true|false,"concern":"short","alternate_view":true|false,"nuance":"one sentence or empty"}'
    )
    user = (
        f"User: {user_message[:800]}\n"
        f"Genesis ({chosen_employee}) answered: {draft_answer[:1200]}\n"
        "Is this helpful, accurate enough, and respectful? If debate topic — note alternate view."
    )
    try:
        result = juror.chat(
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        parsed = _parse_jury_json(result.answer)
    except (httpx.HTTPError, OSError, KeyError, AttributeError) as exc:
        logger.debug("AI Jury skip: %s", exc)
        return JuryVerdict(invoked=False)

    agrees = bool(parsed.get("agrees", True))
    concern = str(parsed.get("concern") or "")[:240]
    alternate = bool(parsed.get("alternate_view"))
    nuance = str(parsed.get("nuance") or parsed.get("suggested_fix") or "")[:320]
    return JuryVerdict(
        invoked=True,
        juror_id=juror.provider_id,
        agrees=agrees,
        concern=concern,
        nuance=nuance,
        alternate_view=alternate,
    )


def apply_jury(answer: str, jury: JuryVerdict) -> str:
    if not jury.invoked or jury.agrees or not jury.nuance.strip():
        return answer
    text = answer.rstrip()
    if jury.alternate_view:
        return f"{text}\n\n{jury.nuance.strip()}"
    if len(jury.nuance) < 220:
        return f"{text}\n\n{jury.nuance.strip()}"
    return answer
