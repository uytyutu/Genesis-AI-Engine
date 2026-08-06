"""Opportunity Normalizer — one shape for all Tier A sources."""

from __future__ import annotations

from typing import Any


REQUIRED_FIELDS = (
    "id",
    "platform",
    "title",
    "url",
    "reward_usd",
)


def opportunity_key(opp: dict[str, Any]) -> str:
    """Dedupe key: prefer repo+issue, else canonical URL, else id."""
    repo = str(opp.get("repository") or "").strip().lower()
    issue = str(opp.get("issue_id") or "").strip()
    if repo and issue:
        return f"gh:{repo}#{issue}"
    url = str(opp.get("url") or opp.get("issue_url") or "").strip().lower().rstrip("/")
    if url:
        return f"url:{url}"
    return f"id:{opp.get('platform')}:{opp.get('native_id') or opp.get('id')}"


def ensure_opportunity(opp: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(opp, dict):
        return None
    for field in REQUIRED_FIELDS:
        if opp.get(field) in (None, ""):
            return None
    out = dict(opp)
    out.setdefault("native_id", str(out.get("id") or ""))
    out.setdefault("tier", "A")
    out.setdefault("estimated_reward_usd", float(out.get("reward_usd") or 0))
    out.setdefault("real_income", False)
    out.setdefault("issue_url", out.get("url"))
    out.setdefault("languages", [])
    out.setdefault("blockers", [])
    return out


def dedupe_opportunities(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep highest overall_confidence when the same issue appears on multiple platforms."""
    best: dict[str, dict[str, Any]] = {}
    for raw in items:
        opp = ensure_opportunity(raw)
        if not opp:
            continue
        key = opportunity_key(opp)
        prev = best.get(key)
        if prev is None:
            best[key] = opp
            continue
        prev_score = float(prev.get("overall_confidence_pct") or 0)
        new_score = float(opp.get("overall_confidence_pct") or 0)
        prev_reward = float(prev.get("reward_usd") or 0)
        new_reward = float(opp.get("reward_usd") or 0)
        if new_score > prev_score or (
            new_score == prev_score and new_reward > prev_reward
        ):
            # Preserve multi-platform provenance
            sources = list(prev.get("also_on") or [])
            if prev.get("platform") and prev["platform"] != opp.get("platform"):
                sources.append(prev["platform"])
            opp["also_on"] = sorted(set(sources + list(opp.get("also_on") or [])))
            best[key] = opp
        else:
            also = list(prev.get("also_on") or [])
            if opp.get("platform") and opp["platform"] != prev.get("platform"):
                also.append(str(opp["platform"]))
            prev["also_on"] = sorted(set(also))
    return list(best.values())
