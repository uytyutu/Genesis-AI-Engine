"""Farm Execution Manager — AI Software Engineer orchestrator (Opire factory).

Not a single code bot. Chooses tool, can REFUSE, validates, loops, prepares Draft PR.
CEO Approve remains mandatory. Push/Submit PR remain CEO gates.

Tool route (v1):
  refuse          — confidence / stack / scope outside Virtus capability
  local_engineer  — bounded LLM patch via Groq/OpenAI-compatible API (if key)
  needs_external  — process fork → Research Agent + Codex/Groq (or Cursor brief)
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# Hard refuse — even high $ does not override (Farm must say "не могу")
REFUSE_TITLE = re.compile(
    r"kernel\s*driver|device\s*driver|wayland|rcs\s*support|"
    r"web\s*platform\s*export|hcaptcha|recaptcha|captcha|"
    r"burn\s*address|chainparams\.cpp",
    re.I,
)

REFUSE_LANGS = frozenset({"solidity", "haskell", "cobol", "fortran"})

# Stage 3 local engineer — conservative stack for first autonomous loop
LOCAL_ENGINEER_LANGS = frozenset(
    {"python", "javascript", "typescript", "html", "css", "mdx", "php", "go"}
)

MIN_LOCAL_CONFIDENCE = 78.0
MAX_RELATED_FILES_READ = 8
MAX_FILE_CHARS = 12_000
MAX_PATCH_FILES = 6


def estimate_execution(task: dict[str, Any]) -> dict[str, Any]:
    """Probability + time — CEO sees realistic factory metrics, not vibes."""
    overall = float(task.get("overall_confidence_pct") or 0)
    hours = float(task.get("estimated_hours") or 1.0)
    competitors = int(task.get("competitors") or 0)
    reward = float(task.get("reward_usd") or task.get("estimated_reward_usd") or 0)

    # Success = engine can ship a mergeable PR; acceptance = maintainer likely merges
    success = overall
    acceptance = float(task.get("acceptance_pct") or overall * 0.9)
    if competitors >= 5:
        success *= 0.85
        acceptance *= 0.8
    if reward >= 1000:
        # Larger bounty → more scrutiny; still allowed if confidence high
        success *= 0.92
        hours = max(hours, 4.0)

    success = round(max(5.0, min(97.0, success)), 1)
    acceptance = round(max(5.0, min(95.0, acceptance)), 1)
    return {
        "success_probability_pct": success,
        "acceptance_probability_pct": acceptance,
        "estimated_hours": round(hours, 1),
        "estimated_minutes": int(round(hours * 60)),
        "reward_usd": reward,
        "note_ru": (
            "Оценка вероятности выполнения Virtus (не гарантия merge/payout). "
            "Estimated ≠ REAL."
        ),
    }


def _has_engineer_llm() -> bool:
    from swarm.farm_env_bootstrap import ensure_farm_env

    ensure_farm_env()
    return bool(
        (
            os.environ.get("GROQ_API_KEY")
            or os.environ.get("GENESIS_GROQ_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("GENESIS_LLM_API_KEY")
            or ""
        ).strip()
    )


def capability_gate(task: dict[str, Any], stack: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return route: refuse | local_engineer | needs_external."""
    title = str(task.get("title") or "")
    body = str(task.get("issue_body_preview") or "")
    langs = {str(x).lower() for x in (task.get("languages") or [])}
    overall = float(task.get("overall_confidence_pct") or 0)
    blockers = list(task.get("blockers") or [])
    stack_langs = set((stack or {}).get("languages") or [])

    reasons: list[str] = []
    if blockers:
        reasons.extend(f"blocker:{b}" for b in blockers)
    if REFUSE_TITLE.search(title) or REFUSE_TITLE.search(body):
        reasons.append("hard_refuse_pattern")
    if langs & REFUSE_LANGS:
        reasons.append(f"refuse_language:{sorted(langs & REFUSE_LANGS)}")
    if overall < 55.0:
        reasons.append("confidence_too_low")

    if reasons:
        return {
            "route": "refuse",
            "can_execute": False,
            "reasons": reasons,
            "recommendation": "SKIP",
            "message_ru": (
                "Farm Engine отказывается: задача вне компетенции или слишком рискованна. "
                + "; ".join(reasons[:4])
            ),
        }

    effective_langs = langs or stack_langs
    local_ok = (
        overall >= MIN_LOCAL_CONFIDENCE
        and (not effective_langs or bool(effective_langs & LOCAL_ENGINEER_LANGS))
        and "large_feature_risk" not in blockers
    )
    if local_ok and _has_engineer_llm():
        return {
            "route": "local_engineer",
            "can_execute": True,
            "reasons": ["high_confidence_supported_stack", "llm_available"],
            "recommendation": "TAKE",
            "message_ru": "Локальный engineer-loop (LLM patch → tests → commit).",
            "tools": ["local_engineer", "tests", "git_commit"],
        }

    if local_ok and not _has_engineer_llm():
        return {
            "route": "needs_external",
            "can_execute": True,
            "reasons": ["llm_key_missing_use_cursor_codex"],
            "recommendation": "REVIEW",
            "message_ru": (
                "Стек подходит, но нет API-ключа engineer LLM. "
                "Research Agent / Codex недоступны — brief для Cursor."
            ),
            "tools": ["cursor", "codex", "research_agent"],
        }

    return {
        "route": "needs_external",
        "can_execute": True,
        "reasons": ["prefer_cursor_or_codex"],
        "recommendation": "REVIEW",
        "message_ru": (
            "Развилка needs_external: Local Engineer недостаточен. "
            "Запустится Research Agent + Codex/Groq (если есть ключ), иначе Cursor brief."
        ),
        "tools": ["research_agent", "codex", "cursor", "vector_orchestrator"],
    }


def _llm_chat(
    system: str,
    user: str,
    *,
    timeout: float = 90.0,
    preferred_provider: str | None = None,
) -> dict[str, Any]:
    """Thin OpenAI-compatible call. preferred_provider: openai|groq|None(auto)."""
    from swarm.farm_env_bootstrap import ensure_farm_env

    ensure_farm_env()
    groq_key = (
        os.environ.get("GROQ_API_KEY") or os.environ.get("GENESIS_GROQ_API_KEY") or ""
    ).strip()
    openai_key = (
        os.environ.get("OPENAI_API_KEY") or os.environ.get("GENESIS_LLM_API_KEY") or ""
    ).strip()

    use_openai = False
    if preferred_provider in ("openai", "codex"):
        use_openai = bool(openai_key)
        if not use_openai and not groq_key:
            return {"ok": False, "error": "no_llm_api_key", "text": ""}
        if not use_openai:
            use_openai = False  # fall through to groq
    elif preferred_provider == "groq":
        use_openai = False if groq_key else bool(openai_key)
    else:
        # auto: groq first (cheaper/fast), else openai
        use_openai = not groq_key and bool(openai_key)

    if use_openai:
        key = openai_key
        if not key:
            return {"ok": False, "error": "no_llm_api_key", "text": ""}
        base = (
            os.environ.get("GENESIS_LLM_BASE_URL") or "https://api.openai.com/v1"
        ).rstrip("/")
        model = (
            os.environ.get("FARM_CODEX_MODEL")
            or os.environ.get("FARM_ENGINEER_MODEL")
            or os.environ.get("GENESIS_LLM_MODEL")
            or "gpt-4o-mini"
        )
    else:
        key = groq_key or openai_key
        if not key:
            return {"ok": False, "error": "no_llm_api_key", "text": ""}
        if groq_key:
            base = (
                os.environ.get("GENESIS_GROQ_BASE_URL")
                or os.environ.get("GROQ_BASE_URL")
                or "https://api.groq.com/openai/v1"
            ).rstrip("/")
            model = (
                os.environ.get("FARM_ENGINEER_MODEL")
                or os.environ.get("GENESIS_GROQ_MODEL")
                or "llama-3.3-70b-versatile"
            )
        else:
            base = (
                os.environ.get("GENESIS_LLM_BASE_URL") or "https://api.openai.com/v1"
            ).rstrip("/")
            model = (
                os.environ.get("FARM_CODEX_MODEL")
                or os.environ.get("FARM_ENGINEER_MODEL")
                or os.environ.get("GENESIS_LLM_MODEL")
                or "gpt-4o-mini"
            )

    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "VirtusCore-FarmExecutionManager/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = (
            ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        )
        return {"ok": True, "error": None, "text": text, "model": model}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http_{exc.code}", "text": ""}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "text": ""}


def _read_context_files(root: Path, related: list[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for rel in related[:MAX_RELATED_FILES_READ]:
        path = root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        out.append({"path": rel.replace("\\", "/"), "content": text[:MAX_FILE_CHARS]})
    return out


def _parse_patch_json(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    # Strip markdown fences
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fence:
        raw = fence.group(1).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try first {...} blob
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict):
        return None
    return data


def apply_file_patches(root: Path, files: list[dict[str, Any]]) -> dict[str, Any]:
    touched: list[str] = []
    errors: list[str] = []
    for item in files[:MAX_PATCH_FILES]:
        if not isinstance(item, dict):
            continue
        rel = str(item.get("path") or "").replace("\\", "/").lstrip("/")
        if not rel or ".." in rel.split("/"):
            errors.append(f"bad_path:{rel}")
            continue
        content = item.get("content")
        if content is None:
            errors.append(f"missing_content:{rel}")
            continue
        dest = root / rel
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(str(content), encoding="utf-8")
            touched.append(rel)
        except OSError as exc:
            errors.append(f"write_failed:{rel}:{exc}")
    return {"ok": bool(touched) and not errors, "touched": touched, "errors": errors}


def build_external_brief(task: dict[str, Any], plan: dict[str, Any]) -> str:
    return (
        "# Farm Engine — External Tool Brief (Cursor / Codex)\n\n"
        f"**Title:** {task.get('title')}\n"
        f"**Issue:** {task.get('issue_url') or task.get('url')}\n"
        f"**Repo:** {task.get('repository')}\n"
        f"**Reward (estimated):** ${task.get('reward_usd')}\n"
        f"**Confidence:** {task.get('overall_confidence_pct')}%\n\n"
        "## Plan\n"
        + "\n".join(f"- {s.get('title')}" for s in (plan.get("steps") or []))
        + "\n\n## Issue preview\n"
        + str(task.get("issue_body_preview") or "")[:2000]
        + "\n\n## Rules\n"
        "- Official Opire: comment `/try` on Issue, PR body `/claim #<n>`.\n"
        "- Minimal diff. No unrelated refactors.\n"
        "- Run tests before Draft PR.\n"
        "- Farm does NOT mark REAL until payout confirmed.\n"
    )


def run_local_engineer_once(
    *,
    root: Path,
    task: dict[str, Any],
    plan: dict[str, Any],
    related: list[str],
    repair_feedback: str = "",
) -> dict[str, Any]:
    """One generation attempt → file patches. May return cannot=true."""
    ctx = _read_context_files(root, related)
    system = (
        "You are a senior software engineer (50 years equivalent discipline). "
        "Produce a MINIMAL fix for the GitHub issue. "
        "Reply with ONLY JSON: "
        '{"cannot": false, "cannot_reason": "", "summary": "...", '
        '"files": [{"path": "relative/path", "content": "full new file content"}]}. '
        "If you cannot safely solve it, set cannot=true and explain. "
        "Do not invent APIs. Do not touch unrelated files. "
        "Never weaken or delete tests to make them pass — fix production code. "
        "Prefer editing implementation files over test files. "
        "No captcha/ToS bypass. No secrets."
    )
    user = json.dumps(
        {
            "title": task.get("title"),
            "issue_url": task.get("issue_url") or task.get("url"),
            "issue_body_preview": (task.get("issue_body_preview") or "")[:3000],
            "plan": plan,
            "related_files": ctx,
            "repair_feedback": repair_feedback[:2000],
        },
        ensure_ascii=False,
    )
    llm = _llm_chat(system, user)
    if not llm.get("ok"):
        return {
            "ok": False,
            "cannot": True,
            "cannot_reason": llm.get("error") or "llm_unavailable",
            "touched": [],
            "llm": llm,
        }
    parsed = _parse_patch_json(str(llm.get("text") or ""))
    if not parsed:
        return {
            "ok": False,
            "cannot": True,
            "cannot_reason": "invalid_llm_json",
            "touched": [],
            "llm": llm,
        }
    if parsed.get("cannot"):
        return {
            "ok": False,
            "cannot": True,
            "cannot_reason": str(parsed.get("cannot_reason") or "model_refused"),
            "touched": [],
            "summary": parsed.get("summary"),
            "llm": llm,
        }
    files = parsed.get("files") or []
    if not isinstance(files, list) or not files:
        return {
            "ok": False,
            "cannot": True,
            "cannot_reason": "empty_patch",
            "touched": [],
            "llm": llm,
        }
    applied = apply_file_patches(root, files)
    return {
        "ok": applied["ok"],
        "cannot": False,
        "cannot_reason": "",
        "touched": applied.get("touched") or [],
        "errors": applied.get("errors") or [],
        "summary": parsed.get("summary"),
        "llm_model": llm.get("model"),
    }


class ExecutionManager:
    """Orchestrates Stage 3+ for one approved Opire task."""

    def decide_route(
        self, task: dict[str, Any], stack: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        estimate = estimate_execution(task)
        gate = capability_gate(task, stack)
        return {**gate, "estimate": estimate}

    def prepare_external_package(
        self, workspace: Path, task: dict[str, Any], plan: dict[str, Any]
    ) -> dict[str, Any]:
        brief = build_external_brief(task, plan)
        path = workspace / "EXTERNAL_TOOL_BRIEF.md"
        path.write_text(brief, encoding="utf-8")
        return {"ok": True, "brief_path": str(path), "mode": "needs_external"}
