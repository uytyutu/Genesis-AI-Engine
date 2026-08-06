"""Opire Farm Pre-flight — answer before Approve: should we take this bounty?

Verdicts:
  GO     — critical checks pass, auto Execution allowed
  REVIEW — soft doubts (CEO may still Approve)
  SKIP   — critical failure (Approve blocked)
"""

from __future__ import annotations

from typing import Any

from swarm.farm_virtus_capabilities import (
    detect_task_type,
    task_type_auto_ok,
)


def _check(
    id: str,
    label: str,
    *,
    ok: bool,
    critical: bool = False,
    detail: str = "",
) -> dict[str, Any]:
    return {
        "id": id,
        "label": label,
        "ok": ok,
        "critical": critical,
        "detail": detail,
        "mark": "✅" if ok else ("⛔" if critical else "⚠"),
    }


def run_preflight(
    cand: dict[str, Any],
    *,
    deep: bool = False,
    min_confidence: float = 80.0,
) -> dict[str, Any]:
    """Build Pre-flight checklist from candidate (+ optional deep GitHub probes)."""
    blockers = {str(b) for b in (cand.get("blockers") or [])}
    reasons = {str(r) for r in (cand.get("reject_reasons") or [])}
    conf = float(
        cand.get("overall_confidence_pct")
        or cand.get("success_probability_pct")
        or 0
    )
    repo_status = str(cand.get("repo_status") or "")
    probe = cand.get("repo_probe") if isinstance(cand.get("repo_probe"), dict) else {}
    hours = float(cand.get("estimated_hours") or 99)
    comps = int(cand.get("competitors") or 0)
    langs = [str(x).lower() for x in (cand.get("languages") or [])]
    supported = [str(x).lower() for x in (cand.get("supported_languages") or [])]
    title = str(cand.get("title") or "")
    task_type = str(cand.get("task_type") or detect_task_type(title, langs))
    auto_cap = task_type_auto_ok(task_type)

    repo_alive = (
        repo_status in ("", "ok", "unknown")
        and "repo_unreachable" not in blockers
        and "missing_repo" not in blockers
        and probe.get("error_code") not in ("repo_not_found", "repo_unreachable", "missing_repo")
    )
    issue_open = "issue_closed" not in blockers and bool(cand.get("url") or cand.get("issue_url"))
    lang_ok = (
        "unsupported_language" not in blockers
        and (bool(supported) or not langs or auto_cap.get("ok"))
    )
    small_patch = (
        hours <= 6
        and "large_feature_risk" not in blockers
        and "reward_implies_large_scope" not in blockers
    )
    low_comp = comps <= 2 and "high_competition" not in blockers
    conf_ok = conf >= min_confidence and "review_band" not in reasons
    no_forbidden = "forbidden_captcha_or_tos_evasion" not in blockers

    checks = [
        _check("repo_alive", "Repository доступен", ok=repo_alive, critical=True),
        _check("issue_open", "Issue открыта / URL есть", ok=issue_open, critical=True),
        _check(
            "no_forbidden",
            "Нет forbidden / ToS evasion",
            ok=no_forbidden,
            critical=True,
        ),
        _check(
            "language",
            "Language / capability supported",
            ok=lang_ok,
            critical=True,
            detail=", ".join(supported or langs) or task_type,
        ),
        _check(
            "task_type",
            f"Task type: {task_type}",
            ok=bool(auto_cap.get("ok")),
            critical=auto_cap.get("severity") == "❌",
            detail=str(auto_cap.get("note_ru") or ""),
        ),
        _check(
            "small_patch",
            "Estimated patch small",
            ok=small_patch,
            critical=False,
            detail=f"~{hours}h",
        ),
        _check(
            "low_competition",
            "Нет высокой конкуренции",
            ok=low_comp,
            critical=False,
            detail=f"competitors={comps}",
        ),
        _check(
            "confidence",
            f"Confidence ≥ {min_confidence:.0f}%",
            ok=conf_ok,
            critical=False,
            detail=f"{conf:.0f}%",
        ),
    ]

    # Deep: conflicting open PRs mentioning same issue
    conflict_ok = True
    conflict_detail = "not probed"
    if deep:
        conflict = _probe_conflicting_prs(cand, timeout=6.0)
        conflict_ok = bool(conflict.get("ok", True))
        conflict_detail = str(conflict.get("detail") or "")
        checks.append(
            _check(
                "no_conflicting_pr",
                "Нет конкурирующего PR",
                ok=conflict_ok,
                critical=False,
                detail=conflict_detail,
            )
        )
    else:
        checks.append(
            _check(
                "no_conflicting_pr",
                "Нет конкурирующего PR",
                ok=True,
                critical=False,
                detail="probe on Approve",
            )
        )

    critical_fail = [c for c in checks if c["critical"] and not c["ok"]]
    soft_fail = [c for c in checks if not c["critical"] and not c["ok"]]

    if critical_fail:
        verdict = "SKIP"
        action = f"SKIP — {critical_fail[0]['label']}"
    elif soft_fail and not conf_ok:
        verdict = "REVIEW"
        action = "REVIEW — soft checks failed"
    elif soft_fail:
        verdict = "REVIEW"
        action = "REVIEW — " + ", ".join(c["id"] for c in soft_fail[:3])
    else:
        verdict = "GO"
        action = "GO — Pre-flight passed"

    return {
        "ok": True,
        "verdict": verdict,
        "go": verdict == "GO",
        "approve_allowed": verdict in ("GO", "REVIEW"),
        "auto_execute_allowed": verdict == "GO",
        "action": action,
        "checks": checks,
        "task_type": task_type,
        "capability": auto_cap,
        "min_confidence": min_confidence,
        "note_ru": (
            "Pre-flight до Approve: GO → можно Execution; "
            "SKIP → Approve запрещён; REVIEW → только ручной риск CEO."
        ),
    }


def _probe_conflicting_prs(cand: dict[str, Any], *, timeout: float = 6.0) -> dict[str, Any]:
    """Best-effort: open PRs that reference the same issue number."""
    repo = str(cand.get("repository") or "")
    issue_id = str(cand.get("issue_id") or "")
    if not repo or "/" not in repo or not issue_id:
        return {"ok": True, "detail": "no repo/issue to probe"}
    try:
        import json
        import urllib.request

        from swarm.opire_issue_intel import _github_api_headers

        owner, name = repo.split("/", 1)
        url = (
            f"https://api.github.com/repos/{owner}/{name}/pulls"
            f"?state=open&per_page=30"
        )
        req = urllib.request.Request(url, headers=_github_api_headers())
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            pulls = json.loads(resp.read().decode("utf-8"))
        if not isinstance(pulls, list):
            return {"ok": True, "detail": "unexpected PR payload"}
        needle = f"#{issue_id}"
        hits = []
        for pr in pulls:
            blob = f"{pr.get('title') or ''} {pr.get('body') or ''}"
            if needle in blob or f"/{issue_id}" in blob:
                hits.append(str(pr.get("html_url") or pr.get("number")))
        if hits:
            return {
                "ok": False,
                "detail": f"open PR refs issue: {hits[0]}",
                "prs": hits[:5],
            }
        return {"ok": True, "detail": f"no open PR refs #{issue_id}"}
    except Exception as exc:  # noqa: BLE001
        # Soft: network failure does not block Approve
        return {"ok": True, "detail": f"probe skipped: {exc}"[:160]}
