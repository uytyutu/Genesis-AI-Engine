"""Farm Research Agent + Codex executor — needs_external process fork.

When Local Engineer is insufficient, Research Agent:
  1) studies repo context (README / docs / related files)
  2) writes RESEARCH_BRIEF.md + change plan
  3) optionally emits a minimal docs/code patch
  4) hands off to Codex (OpenAI) or Groq engineer for a second pass

This is NOT Cursor desktop automation — API executors only.
CEO Submit / push remain mandatory gates. Estimated ≠ REAL.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from swarm.farm_execution_manager import (
    MAX_FILE_CHARS,
    MAX_RELATED_FILES_READ,
    _llm_chat,
    _parse_patch_json,
    _read_context_files,
    apply_file_patches,
    run_local_engineer_once,
)

RESEARCH_HINT = re.compile(
    r"\bresearch\b|\binvestigat|\bfeasibility\b|\bdesign\s+note\b|"
    r"\bdocument(?:ation)?\b|\bdocs?\b|\bwindows\s+support\b|\broadmap\b",
    re.I,
)

# Extra roots to sample for research (beyond related heuristics)
_DOC_GLOBS = (
    "README.md",
    "README.rst",
    "CONTRIBUTING.md",
    "docs/**/*.md",
    "doc/**/*.md",
)


def auto_research_enabled() -> bool:
    from swarm.farm_env_bootstrap import ensure_farm_env

    ensure_farm_env()
    flag = (os.environ.get("FARM_AUTO_RESEARCH") or "1").strip().lower()
    return flag not in ("0", "false", "no", "off")


def pick_executor() -> str:
    """Return codex | groq | none — preferred API worker for research/codegen.

    Prefer a *healthy* path: if OpenAI is rate-limited recently, Groq may still work.
    Override with FARM_EXECUTOR=codex|groq|auto.
    """
    from swarm.farm_env_bootstrap import ensure_farm_env

    ensure_farm_env()
    forced = (os.environ.get("FARM_EXECUTOR") or "auto").strip().lower()
    has_openai = bool(
        (
            os.environ.get("OPENAI_API_KEY")
            or os.environ.get("GENESIS_LLM_API_KEY")
            or ""
        ).strip()
    )
    has_groq = bool(
        (
            os.environ.get("GROQ_API_KEY")
            or os.environ.get("GENESIS_GROQ_API_KEY")
            or ""
        ).strip()
    )
    # Prefer Groq when both present — OpenAI free/tier often 429s; Codex still
    # available via fallback inside _llm_chat_executor when forced=codex.
    prefer = (os.environ.get("FARM_EXECUTOR_PREFER") or "groq").strip().lower()
    if forced in ("codex", "openai"):
        return "codex" if has_openai else ("groq" if has_groq else "none")
    if forced in ("groq", "local_engineer"):
        return "groq" if has_groq else ("codex" if has_openai else "none")
    if prefer == "codex":
        if has_openai:
            return "codex"
        if has_groq:
            return "groq"
        return "none"
    # auto default: groq first when available
    if has_groq:
        return "groq"
    if has_openai:
        return "codex"
    return "none"


def _llm_chat_executor(
    system: str, user: str, *, executor: str, timeout: float = 120.0
) -> dict[str, Any]:
    """Route chat to Codex (OpenAI) or Groq; auto-fallback on rate-limit/HTTP errors."""
    order: list[str] = []
    if executor == "codex":
        order = ["codex", "groq"]
    elif executor == "groq":
        order = ["groq", "codex"]
    else:
        return {"ok": False, "error": "no_executor", "text": ""}

    last: dict[str, Any] = {"ok": False, "error": "no_executor", "text": ""}
    for name in order:
        preferred = "openai" if name == "codex" else "groq"
        last = _llm_chat(system, user, timeout=timeout, preferred_provider=preferred)
        if last.get("ok"):
            last = dict(last)
            last["executor_used"] = name
            return last
        err = str(last.get("error") or "")
        # Retry other provider on rate-limit / auth / transient HTTP
        if err.startswith("http_429") or err.startswith("http_5") or err in (
            "no_llm_api_key",
            "http_401",
            "http_403",
        ):
            continue
        break
    last = dict(last)
    last["executor_used"] = order[0]
    return last


def _discover_doc_paths(root: Path, limit: int = 6) -> list[str]:
    found: list[str] = []
    for name in ("README.md", "README.rst", "CONTRIBUTING.md"):
        if (root / name).is_file():
            found.append(name)
    docs = root / "docs"
    if docs.is_dir():
        for p in sorted(docs.rglob("*.md"))[:limit]:
            rel = str(p.relative_to(root)).replace("\\", "/")
            if rel not in found:
                found.append(rel)
    return found[: MAX_RELATED_FILES_READ]


def looks_like_research_task(task: dict[str, Any]) -> bool:
    blob = f"{task.get('title') or ''} {task.get('issue_body_preview') or ''}"
    return bool(RESEARCH_HINT.search(blob))


def run_research_agent(
    *,
    root: Path,
    workspace: Path,
    task: dict[str, Any],
    plan: dict[str, Any],
    related: list[str],
    executor: str | None = None,
) -> dict[str, Any]:
    """Study repo → RESEARCH_BRIEF.md → optional minimal files patch."""
    executor = executor or pick_executor()
    if executor == "none":
        return {
            "ok": False,
            "stage": "research",
            "executor": "none",
            "error": "no_llm_api_key",
            "message_ru": (
                "Research Agent: нет OPENAI/GROQ ключа — brief для Cursor остаётся ручным."
            ),
            "can_generate_patch": False,
            "files_touched": [],
        }

    related_all = list(dict.fromkeys([*related, *_discover_doc_paths(root)]))
    ctx = _read_context_files(root, related_all)
    system = (
        "You are Virtus Core Research Agent for open-source bounties. "
        "Study the issue and repository context. "
        "Reply with ONLY JSON:\n"
        "{"
        '"cannot": false, '
        '"summary": "one paragraph", '
        '"research_markdown": "# Research brief\\n...", '
        '"change_plan": ["step1", "step2"], '
        '"recommended_files": ["path"], '
        '"can_generate_patch": true|false, '
        '"docs_only": true|false, '
        '"files": [{"path": "relative/path", "content": "full file content"}]'
        "}\n"
        "Rules:\n"
        "- Prefer documentation / research notes when the issue asks for research.\n"
        "- If a safe minimal code/docs patch is clear, put it in files[].\n"
        "- If unsafe or incomplete, set can_generate_patch=false and files=[].\n"
        "- Never invent APIs. Never weaken tests. No secrets. Minimal diff.\n"
        "- research_markdown must be honest: state what is NOT verified."
    )
    user = json.dumps(
        {
            "title": task.get("title"),
            "issue_url": task.get("issue_url") or task.get("url"),
            "repository": task.get("repository"),
            "issue_body_preview": (task.get("issue_body_preview") or "")[:4000],
            "plan": plan,
            "related_files": [
                {"path": c["path"], "content": c["content"][:MAX_FILE_CHARS]}
                for c in ctx
            ],
            "hint_research_issue": looks_like_research_task(task),
        },
        ensure_ascii=False,
    )
    llm = _llm_chat_executor(system, user, executor=executor, timeout=150.0)
    if not llm.get("ok"):
        return {
            "ok": False,
            "stage": "research",
            "executor": executor,
            "error": llm.get("error") or "llm_failed",
            "message_ru": "Research Agent не получил ответ от API.",
            "can_generate_patch": False,
            "files_touched": [],
            "llm": {"model": llm.get("model"), "error": llm.get("error")},
        }

    parsed = _parse_patch_json(str(llm.get("text") or ""))
    if not parsed:
        return {
            "ok": False,
            "stage": "research",
            "executor": executor,
            "error": "invalid_llm_json",
            "message_ru": "Research Agent вернул невалидный JSON.",
            "can_generate_patch": False,
            "files_touched": [],
        }

    research_md = str(parsed.get("research_markdown") or "").strip()
    if not research_md:
        research_md = (
            f"# Research brief\n\n{parsed.get('summary') or 'No summary.'}\n\n"
            "## Change plan\n"
            + "\n".join(f"- {s}" for s in (parsed.get("change_plan") or []))
        )
    brief_path = workspace / "RESEARCH_BRIEF.md"
    brief_path.write_text(
        research_md
        + "\n\n---\n"
        f"Executor: `{executor}` · model: `{llm.get('model')}`\n"
        "Farm does NOT mark REAL until payout confirmed.\n",
        encoding="utf-8",
    )

    files = parsed.get("files") or []
    touched: list[str] = []
    apply_errors: list[str] = []
    if isinstance(files, list) and files and not parsed.get("cannot"):
        applied = apply_file_patches(root, files)
        touched = list(applied.get("touched") or [])
        apply_errors = list(applied.get("errors") or [])

    can_patch = bool(parsed.get("can_generate_patch")) or bool(touched)
    if parsed.get("cannot"):
        can_patch = False

    return {
        "ok": True,
        "stage": "research",
        "executor": executor,
        "brief_path": str(brief_path),
        "summary": parsed.get("summary"),
        "change_plan": parsed.get("change_plan") or [],
        "recommended_files": parsed.get("recommended_files") or [],
        "can_generate_patch": can_patch,
        "docs_only": bool(parsed.get("docs_only")),
        "files_touched": touched,
        "apply_errors": apply_errors,
        "cannot": bool(parsed.get("cannot")),
        "cannot_reason": parsed.get("cannot_reason"),
        "message_ru": (
            "Research Agent подготовил RESEARCH_BRIEF"
            + (f" и патч ({len(touched)} файл.)" if touched else " (патча пока нет).")
        ),
        "llm_model": llm.get("model"),
    }


def run_codex_engineer_once(
    *,
    root: Path,
    task: dict[str, Any],
    plan: dict[str, Any],
    related: list[str],
    research: dict[str, Any] | None = None,
    repair_feedback: str = "",
) -> dict[str, Any]:
    """Codex/OpenAI-backed engineer pass (same JSON contract as local engineer)."""
    ctx = _read_context_files(root, related)
    system = (
        "You are Codex acting as Virtus Farm software engineer. "
        "Produce a MINIMAL fix for the GitHub issue. "
        "Reply with ONLY JSON: "
        '{"cannot": false, "cannot_reason": "", "summary": "...", '
        '"files": [{"path": "relative/path", "content": "full new file content"}]}. '
        "If you cannot safely solve it, set cannot=true. "
        "Use the research brief when provided. "
        "Do not invent APIs. Prefer docs when issue is research. "
        "Never weaken tests. No secrets."
    )
    user = json.dumps(
        {
            "title": task.get("title"),
            "issue_url": task.get("issue_url") or task.get("url"),
            "issue_body_preview": (task.get("issue_body_preview") or "")[:3000],
            "plan": plan,
            "research_summary": (research or {}).get("summary"),
            "research_change_plan": (research or {}).get("change_plan"),
            "research_brief_excerpt": _brief_excerpt(research),
            "related_files": ctx,
            "repair_feedback": repair_feedback[:2000],
        },
        ensure_ascii=False,
    )
    llm = _llm_chat_executor(system, user, executor="codex", timeout=150.0)
    if not llm.get("ok"):
        return {
            "ok": False,
            "cannot": True,
            "cannot_reason": llm.get("error") or "codex_unavailable",
            "touched": [],
            "llm": llm,
            "executor": "codex",
        }
    parsed = _parse_patch_json(str(llm.get("text") or ""))
    if not parsed:
        return {
            "ok": False,
            "cannot": True,
            "cannot_reason": "invalid_llm_json",
            "touched": [],
            "llm": llm,
            "executor": "codex",
        }
    if parsed.get("cannot"):
        return {
            "ok": False,
            "cannot": True,
            "cannot_reason": str(parsed.get("cannot_reason") or "model_refused"),
            "touched": [],
            "summary": parsed.get("summary"),
            "llm": llm,
            "executor": "codex",
        }
    files = parsed.get("files") or []
    if not isinstance(files, list) or not files:
        return {
            "ok": False,
            "cannot": True,
            "cannot_reason": "empty_patch",
            "touched": [],
            "llm": llm,
            "executor": "codex",
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
        "executor": "codex",
    }


def _brief_excerpt(research: dict[str, Any] | None, limit: int = 3500) -> str:
    if not research:
        return ""
    path = research.get("brief_path")
    if path and Path(path).is_file():
        try:
            return Path(path).read_text(encoding="utf-8", errors="replace")[:limit]
        except OSError:
            pass
    return str(research.get("summary") or "")[:limit]


def run_followup_engineer(
    *,
    root: Path,
    task: dict[str, Any],
    plan: dict[str, Any],
    related: list[str],
    research: dict[str, Any],
    executor: str | None = None,
    repair_feedback: str = "",
) -> dict[str, Any]:
    """Second pass after research: Codex preferred, else Groq local engineer."""
    executor = executor or pick_executor()
    enriched_plan = dict(plan)
    enriched_plan["research_change_plan"] = research.get("change_plan") or []
    enriched_plan["research_summary"] = research.get("summary")
    feedback = repair_feedback
    brief_bit = _brief_excerpt(research, 2000)
    if brief_bit:
        feedback = (feedback + "\n\nRESEARCH_BRIEF:\n" + brief_bit).strip()

    if executor == "codex":
        return run_codex_engineer_once(
            root=root,
            task=task,
            plan=enriched_plan,
            related=list(
                dict.fromkeys(
                    [
                        *related,
                        *(research.get("recommended_files") or []),
                    ]
                )
            ),
            research=research,
            repair_feedback=feedback,
        )
    if executor == "groq":
        return run_local_engineer_once(
            root=root,
            task=task,
            plan=enriched_plan,
            related=list(
                dict.fromkeys(
                    [
                        *related,
                        *(research.get("recommended_files") or []),
                    ]
                )
            ),
            repair_feedback=feedback,
        )
    return {
        "ok": False,
        "cannot": True,
        "cannot_reason": "no_executor",
        "touched": [],
        "executor": "none",
    }
