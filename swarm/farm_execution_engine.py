"""Farm Execution Engine v1 — post-Approve work for Opire/GitHub bounties.

CEO Approve remains mandatory. Auto-publish / claim only after CEO Submit.

Stages:
  1 Repository Intelligence — clone, stack map, test discovery
  2 Planning — issue → related paths → step plan + risk
  3 Implementation — branch + bounded edits (v1: plan + branch; codegen loop next)
  4 Validation — lint/tests with retry budget
  5 PR Intelligence — body template, Issue link, /claim, Draft PR metadata
  6 Review Loop — ingest review comments → re-plan (structure ready)

Official Opire: /try on issue → work → PR with /claim #N → merge → payout.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

STAGES = (
    "repo_intelligence",
    "planning",
    "implementation",
    "validation",
    "pr_intelligence",
    "review_loop",
    "awaiting_ceo_submit",
    "submitted",
    "failed",
)

WORK_ROOT_NAME = "opire_workspaces"
MAX_TEST_ATTEMPTS = 3

_GIT_CANDIDATES = (
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files\Git\bin\git.exe",
    r"C:\Program Files (x86)\Git\cmd\git.exe",
    "/usr/bin/git",
    "/usr/local/bin/git",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_git_binary() -> str | None:
    found = shutil.which("git")
    if found:
        return found
    for candidate in _GIT_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    return None


def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 120,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    merged.setdefault("GIT_TERMINAL_PROMPT", "0")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=merged,
        )
        return {
            "ok": proc.returncode == 0,
            "code": proc.returncode,
            "stdout": (proc.stdout or "")[-4000:],
            "stderr": (proc.stderr or "")[-4000:],
            "cmd": cmd,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "code": -1, "stdout": "", "stderr": "timeout", "cmd": cmd}
    except FileNotFoundError as exc:
        return {"ok": False, "code": -2, "stdout": "", "stderr": str(exc), "cmd": cmd}


def _github_token() -> str:
    return (
        os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
        or os.environ.get("GENESIS_GITHUB_TOKEN")
        or ""
    ).strip()


def _authed_github_clone_url(repo_url: str, token: str) -> str | None:
    """Embed token for HTTPS clone without interactive prompt. Never log the result."""
    if not token or "github.com" not in (repo_url or ""):
        return None
    m = re.search(r"github\.com[/:]([^/]+)/([^/\s]+?)(?:\.git)?/?$", (repo_url or "").strip())
    if not m:
        return None
    owner, repo = m.group(1), m.group(2).removesuffix(".git")
    return f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"


def classify_clone_error(stderr: str, *, repo_url: str = "") -> dict[str, str]:
    """Map raw git stderr → stable code + CEO-facing Russian detail."""
    text = (stderr or "").strip()
    low = text.lower()
    repo = (repo_url or "").split("@")[-1] if repo_url else ""
    if "repository not found" in low or "not found" in low and "fatal" in low:
        return {
            "code": "repo_not_found",
            "detail_ru": (
                "Репозиторий недоступен на GitHub (удалён, переименован или private без доступа).\n"
                f"URL: {repo or '—'}\n"
                "Это не сбой Virtus Core — Opire bounty указывает на мёртвый/закрытый repo.\n"
                "Выберите другой bounty или проверьте, что репозиторий публичный."
            ),
        }
    if "authentication failed" in low or "could not read username" in low or "403" in low:
        return {
            "code": "auth_required",
            "detail_ru": (
                "GitHub отклонил clone (нужен доступ).\n"
                "Добавьте GITHUB_TOKEN в dashboard/backend/.env.local и перезапустите Genesis.exe,\n"
                "либо берите только публичные Opire bounty."
            ),
        }
    if "git_not_found" in low or "is not recognized" in low:
        return {
            "code": "git_missing",
            "detail_ru": text or "Git не найден в PATH.",
        }
    return {
        "code": "clone_failed",
        "detail_ru": text[:500] or "git clone failed",
    }


def clone_repository(repo_url: str, dest: Path, *, timeout: int = 180) -> dict[str, Any]:
    """Shallow clone with Windows-safe git resolution. Never prompts for credentials."""
    git = resolve_git_binary()
    if not git:
        return {
            "ok": False,
            "code": -2,
            "stdout": "",
            "stderr": (
                "git_not_found: Git не найден в PATH процесса Genesis. "
                "Установите Git for Windows или добавьте git.exe в PATH, "
                "затем перезапустите Genesis.exe."
            ),
            "cmd": ["git", "clone", repo_url],
            "git_binary": None,
            "error_code": "git_missing",
        }
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = (repo_url or "").strip().rstrip("/")
    if url.startswith("git@github.com:"):
        url = "https://github.com/" + url.removeprefix("git@github.com:")
    if url and "github.com" in url and not url.endswith(".git"):
        url = url.rstrip("/") + ".git"
    res = _run(
        [git, "clone", "--depth", "1", "--single-branch", url, str(dest)],
        timeout=timeout,
    )
    res["git_binary"] = git
    res["repo_url"] = url
    # Private / rate-limited: one retry with token if anonymous clone failed
    if not res["ok"]:
        token = _github_token()
        authed = _authed_github_clone_url(url, token)
        if authed and dest.exists():
            shutil.rmtree(dest, ignore_errors=True)
        if authed:
            res2 = _run(
                [git, "clone", "--depth", "1", "--single-branch", authed, str(dest)],
                timeout=timeout,
            )
            res2["git_binary"] = git
            res2["repo_url"] = url  # never expose token URL
            res2["auth_retry"] = True
            res = res2
    if not res["ok"]:
        classified = classify_clone_error(
            str(res.get("stderr") or res.get("stdout") or ""),
            repo_url=url,
        )
        res["error_code"] = classified["code"]
        res["error_detail_ru"] = classified["detail_ru"]
        if dest.exists():
            shutil.rmtree(dest, ignore_errors=True)
    return res


def detect_stack(root: Path) -> dict[str, Any]:
    files = {p.name.lower() for p in root.iterdir() if p.is_file()} if root.is_dir() else set()
    langs: list[str] = []
    package_managers: list[str] = []
    test_commands: list[list[str]] = []
    lint_commands: list[list[str]] = []

    if "pyproject.toml" in files or "setup.py" in files or "requirements.txt" in files:
        langs.append("python")
        package_managers.append("pip")
        if "pytest.ini" in files or "pyproject.toml" in files or (root / "tests").is_dir():
            test_commands.append(["python", "-m", "pytest", "-q", "--tb=line"])
        lint_commands.append(["python", "-m", "ruff", "check", "."])
    if "package.json" in files:
        langs.append("javascript")
        package_managers.append("npm")
        try:
            pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
            scripts = pkg.get("scripts") or {}
            if "test" in scripts:
                test_commands.append(["npm", "test", "--", "--watchAll=false"])
            if "lint" in scripts:
                lint_commands.append(["npm", "run", "lint"])
            deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
            if "typescript" in deps or (root / "tsconfig.json").exists():
                langs.append("typescript")
        except Exception:
            test_commands.append(["npm", "test"])
    if "go.mod" in files:
        langs.append("go")
        test_commands.append(["go", "test", "./..."])
    if "composer.json" in files:
        langs.append("php")
        package_managers.append("composer")

    # Top-level layout snapshot (bounded)
    top: list[str] = []
    if root.is_dir():
        for p in sorted(root.iterdir(), key=lambda x: x.name.lower())[:40]:
            if p.name.startswith(".git"):
                continue
            top.append(f"{'dir' if p.is_dir() else 'file'}:{p.name}")

    return {
        "languages": sorted(set(langs)),
        "package_managers": package_managers,
        "test_commands": test_commands[:3],
        "lint_commands": lint_commands[:2],
        "top_entries": top,
        "has_tests_guess": bool(test_commands),
    }


def related_paths_heuristic(root: Path, issue_title: str, limit: int = 12) -> list[str]:
    tokens = [
        t
        for t in re.split(r"[^a-zA-Z0-9_]+", (issue_title or "").lower())
        if len(t) >= 4 and t not in {"with", "from", "that", "this", "fix", "issue", "bounty"}
    ]
    hits: list[str] = []
    if not root.is_dir() or not tokens:
        return hits
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.parts):
            continue
        if path.suffix.lower() not in {
            ".py",
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".go",
            ".php",
            ".rs",
            ".java",
        }:
            continue
        name = path.name.lower()
        rel = str(path.relative_to(root)).replace("\\", "/")
        if any(tok in name or tok in rel.lower() for tok in tokens):
            hits.append(rel)
        if len(hits) >= limit:
            break
    return hits


def build_plan(
    *,
    issue_title: str,
    issue_url: str,
    stack: dict[str, Any],
    related: list[str],
) -> dict[str, Any]:
    steps = [
        {
            "id": "read_issue",
            "title": "Read Issue requirements",
            "risk": "low",
            "detail": issue_title,
        },
        {
            "id": "locate_code",
            "title": "Locate change points",
            "risk": "medium",
            "detail": ", ".join(related[:6]) or "manual locate required",
        },
        {
            "id": "implement",
            "title": "Minimal code change (no unrelated edits)",
            "risk": "high",
            "detail": "Execution Engine Stage 3 — bounded patch",
        },
        {
            "id": "validate",
            "title": "Run lint/tests until PASS or retry limit",
            "risk": "medium",
            "detail": str(stack.get("test_commands") or "no test command detected"),
        },
        {
            "id": "draft_pr",
            "title": "Prepare Draft PR + Opire /claim",
            "risk": "low",
            "detail": issue_url,
        },
    ]
    return {
        "summary": f"Plan for: {issue_title}",
        "steps": steps,
        "stack": stack.get("languages") or [],
        "related_files": related,
        "risk_overall": "high" if not related else "medium",
    }


def build_pr_body(*, issue_url: str, issue_id: str, plan: dict[str, Any], title: str) -> str:
    claim = f"/claim #{issue_id}" if issue_id else "/claim"
    steps = "\n".join(f"- {s.get('title')}" for s in (plan.get("steps") or []))
    return (
        f"## Summary\n{title}\n\n"
        f"Fixes: {issue_url}\n\n"
        f"## Plan\n{steps}\n\n"
        f"## Opire\n{claim}\n\n"
        "Prepared by Virtus Core Farm Execution Engine (Draft — CEO Submit required).\n"
    )


class FarmExecutionEngine:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)
        self._root = self._memory / WORK_ROOT_NAME
        self._root.mkdir(parents=True, exist_ok=True)

    def workspace_for(self, reward_id: str) -> Path:
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", reward_id)[:80]
        return self._root / safe

    def run_pipeline(
        self,
        task: dict[str, Any],
        *,
        clone: bool = True,
        max_test_attempts: int = MAX_TEST_ATTEMPTS,
        run_impl: bool = False,
    ) -> dict[str, Any]:
        """Run Stages 1→5 (implementation optional). Never submits PR."""
        started = time.time()
        reward_id = str(task.get("id") or "")
        repo_url = ""
        repo_full = str(task.get("repository") or "")
        if repo_full and "/" in repo_full:
            repo_url = f"https://github.com/{repo_full}.git"
        issue_url = str(task.get("issue_url") or task.get("url") or "")
        issue_id = str(task.get("issue_id") or "")
        title = str(task.get("title") or "bounty")

        report: dict[str, Any] = {
            "ok": False,
            "reward_id": reward_id,
            "stage": "repo_intelligence",
            "stages": {},
            "ceo_submit_required": True,
            "auto_submit_forbidden": True,
            "started_at": _now(),
        }

        ws = self.workspace_for(reward_id)
        src = ws / "src"

        # --- Stage 1: Repository Intelligence ---
        if clone:
            if ws.exists():
                shutil.rmtree(ws, ignore_errors=True)
            ws.mkdir(parents=True, exist_ok=True)
            if not repo_url:
                report["stages"]["repo_intelligence"] = {
                    "ok": False,
                    "error": "missing_repository",
                }
                report["stage"] = "failed"
                report["error"] = "missing_repository"
                report["error_detail"] = "В задаче нет repository (owner/repo)."
                return report
            clone_res = clone_repository(repo_url, src, timeout=180)
            if not clone_res["ok"]:
                detail = (
                    clone_res.get("error_detail_ru")
                    or (clone_res.get("stderr") or clone_res.get("stdout") or "")[:500]
                )
                report["stages"]["repo_intelligence"] = {
                    "ok": False,
                    "clone": {
                        k: v
                        for k, v in clone_res.items()
                        if k != "cmd" or "x-access-token" not in str(v)
                    },
                    "error_detail": detail,
                }
                report["stage"] = "failed"
                report["error"] = clone_res.get("error_code") or "clone_failed"
                report["error_detail"] = detail or "git clone failed"
                report["elapsed_sec"] = round(time.time() - started, 1)
                return report
        elif not src.is_dir():
            report["stages"]["repo_intelligence"] = {"ok": False, "error": "no_workspace"}
            report["stage"] = "failed"
            report["error"] = "no_workspace"
            return report

        stack = detect_stack(src)
        report["stages"]["repo_intelligence"] = {
            "ok": True,
            "workspace": str(src),
            "stack": stack,
            "repo_url": repo_url,
            "git_binary": resolve_git_binary(),
        }

        # --- Stage 2: Planning ---
        related = related_paths_heuristic(src, title)
        plan = build_plan(
            issue_title=title,
            issue_url=issue_url,
            stack=stack,
            related=related,
        )
        plan_path = ws / "EXECUTION_PLAN.json"
        plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        report["stages"]["planning"] = {
            "ok": True,
            "plan_path": str(plan_path),
            "plan": plan,
        }

        # Branch for work
        git = resolve_git_binary() or "git"
        branch = f"virtus/opire-{issue_id or reward_id[:8]}"
        branch = re.sub(r"[^a-zA-Z0-9_./-]+", "-", branch)[:80]
        br = _run([git, "checkout", "-b", branch], cwd=src, timeout=30)
        report["stages"]["branch"] = {"ok": br["ok"], "name": branch, "result": br}

        # --- Stage 3: Execution Manager (orchestrator) ---
        from swarm.farm_execution_manager import ExecutionManager, run_local_engineer_once

        mgr = ExecutionManager()
        route = mgr.decide_route(task, stack)
        report["stages"]["routing"] = route
        report["estimate"] = route.get("estimate")

        impl: dict[str, Any] = {
            "ok": False,
            "route": route.get("route"),
            "files_touched": [],
            "attempts": [],
        }

        if route.get("route") == "refuse":
            impl.update(
                {
                    "ok": False,
                    "mode": "refuse",
                    "message_ru": route.get("message_ru"),
                    "reasons": route.get("reasons"),
                }
            )
            (ws / "IMPLEMENTATION_STATUS.md").write_text(
                "# REFUSE\n\n"
                f"{route.get('message_ru')}\n\n"
                "Farm Engine умеет говорить «не могу». Задача не взята в код.\n",
                encoding="utf-8",
            )
            report["stages"]["implementation"] = impl
            report["ok"] = False
            report["stage"] = "failed"
            report["error"] = "execution_refused"
            report["error_detail"] = route.get("message_ru")
            report["elapsed_sec"] = round(time.time() - started, 1)
            return report

        if route.get("route") == "needs_external":
            from swarm.farm_research_agent import (
                auto_research_enabled,
                pick_executor,
                run_followup_engineer,
                run_research_agent,
            )

            pkg = mgr.prepare_external_package(ws, task, plan)
            executor = pick_executor()
            research_stage: dict[str, Any] = {
                "ok": False,
                "skipped": True,
                "reason": "auto_research_disabled_or_no_key",
            }
            touched_all: list[str] = []
            last_attempt: dict[str, Any] = {}
            followup_mode = "needs_external"

            if run_impl and auto_research_enabled() and executor != "none":
                research_stage = run_research_agent(
                    root=src,
                    workspace=ws,
                    task=task,
                    plan=plan,
                    related=related,
                    executor=executor,
                )
                research_stage["skipped"] = False
                touched_all.extend(research_stage.get("files_touched") or [])

                # Second pass: Codex/Groq engineer using research context
                if research_stage.get("ok") and (
                    research_stage.get("can_generate_patch") or not touched_all
                ):
                    # Always try follow-up when research OK and no files yet;
                    # if research already wrote docs, still allow engineer to extend.
                    for attempt in range(1, max_test_attempts + 1):
                        attempt_res = run_followup_engineer(
                            root=src,
                            task=task,
                            plan=plan,
                            related=related,
                            research=research_stage,
                            executor=executor,
                            repair_feedback="",
                        )
                        impl.setdefault("attempts", []).append(
                            {"n": attempt, "result": attempt_res, "phase": "research_followup"}
                        )
                        last_attempt = attempt_res
                        if attempt_res.get("cannot"):
                            break
                        new_files = attempt_res.get("touched") or []
                        if not new_files:
                            break
                        touched_all.extend(new_files)
                        cmds = list(stack.get("test_commands") or [])
                        if not cmds:
                            break
                        test_res = _run(cmds[0], cwd=src, timeout=300)
                        if test_res["ok"]:
                            break
                        # one repair pass with test stderr
                        attempt_res = run_followup_engineer(
                            root=src,
                            task=task,
                            plan=plan,
                            related=related,
                            research=research_stage,
                            executor=executor,
                            repair_feedback=(
                                f"Tests failed (attempt {attempt}).\n"
                                f"stderr:\n{test_res.get('stderr') or ''}\n"
                                f"stdout:\n{test_res.get('stdout') or ''}"
                            ),
                        )
                        impl.setdefault("attempts", []).append(
                            {
                                "n": f"{attempt}-repair",
                                "result": attempt_res,
                                "phase": "research_followup_repair",
                            }
                        )
                        last_attempt = attempt_res
                        if attempt_res.get("cannot"):
                            break
                        touched_all.extend(attempt_res.get("touched") or [])
                        break

                if touched_all:
                    followup_mode = f"research_then_{executor}"
                else:
                    followup_mode = "needs_external"

            report["stages"]["research"] = research_stage
            impl["files_touched"] = sorted(set(touched_all))
            impl["summary"] = (
                last_attempt.get("summary")
                or research_stage.get("summary")
                or None
            )
            impl["cannot_reason"] = last_attempt.get("cannot_reason")
            impl["executor"] = executor
            impl["brief_path"] = pkg.get("brief_path")
            impl["research_brief_path"] = research_stage.get("brief_path")

            if impl["files_touched"]:
                impl.update(
                    {
                        "ok": True,
                        "mode": followup_mode,
                        "message_ru": (
                            f"Research Agent + {executor}: патч готов "
                            f"({len(impl['files_touched'])} файл.). "
                            "Push/PR — только после CEO Submit."
                        ),
                        "note_ru": research_stage.get("message_ru"),
                    }
                )
                report["stages"]["implementation"] = impl

                (ws / "IMPLEMENTATION_STATUS.md").write_text(
                    "# Implementation Status\n\n"
                    f"Route: `{impl.get('mode')}`\n"
                    f"Executor: `{executor}`\n"
                    f"Issue: {issue_url}\n"
                    f"Branch: `{branch}`\n"
                    f"Files: {', '.join(impl.get('files_touched') or [])}\n"
                    f"Summary: {impl.get('summary') or '—'}\n"
                    f"Research: {research_stage.get('brief_path') or '—'}\n\n"
                    "CEO Submit PR still required. Estimated ≠ REAL.\n",
                    encoding="utf-8",
                )

                # --- Stage 4: Validation ---
                validation = {
                    "ok": True,
                    "attempts": [],
                    "passed": None,
                    "skipped": False,
                }
                cmds = list(stack.get("test_commands") or [])
                if not cmds:
                    validation["skipped"] = True
                    validation["reason"] = "no_test_command_detected"
                    validation["passed"] = True
                else:
                    res = _run(cmds[0], cwd=src, timeout=300)
                    validation["attempts"].append({"n": "final", "result": res})
                    validation["passed"] = bool(res["ok"])
                report["stages"]["validation"] = validation

                for junk in src.rglob("__pycache__"):
                    shutil.rmtree(junk, ignore_errors=True)
                for junk in src.rglob("*.pyc"):
                    try:
                        junk.unlink()
                    except OSError:
                        pass
                _run([git, "add", "-A"], cwd=src, timeout=60)
                commit = _run(
                    [
                        git,
                        "-c",
                        "user.email=farm@virtus.local",
                        "-c",
                        "user.name=Virtus Farm Engine",
                        "commit",
                        "-m",
                        f"fix: {title[:60]} (Opire #{issue_id})",
                    ],
                    cwd=src,
                    timeout=60,
                )
                report["stages"]["commit"] = {
                    "ok": commit["ok"],
                    "result": commit,
                    "pushed": False,
                    "note_ru": "Commit локальный. Push/PR — только после CEO Submit.",
                }
            else:
                # Honest pause — research fork without patch (not a fake success)
                impl.update(
                    {
                        "ok": True,
                        "mode": "needs_external",
                        "message_ru": route.get("message_ru"),
                        "note_ru": (
                            "Развилка needs_external: Research Agent / Codex не получили "
                            "безопасный патч. Файлы репозитория не изменены. "
                            "EXTERNAL_TOOL_BRIEF + RESEARCH_BRIEF (если есть) для Cursor."
                        ),
                        "patch_ready": False,
                    }
                )
                report["stages"]["implementation"] = impl
                validation = {
                    "ok": True,
                    "skipped": True,
                    "reason": "waiting_for_implementation",
                    "passed": None,
                    "attempts": [],
                }
                report["stages"]["validation"] = validation
                report["stages"]["commit"] = {
                    "ok": False,
                    "skipped": True,
                    "reason": "not_created",
                    "pushed": False,
                }
                (ws / "IMPLEMENTATION_STATUS.md").write_text(
                    "# Implementation Status — PAUSED (needs_external)\n\n"
                    "Local Engineer → Research Agent fork.\n"
                    "No repository files modified.\n"
                    "Tests not run.\n"
                    "Nothing pushed to GitHub.\n\n"
                    f"Cursor brief: {pkg.get('brief_path')}\n"
                    f"Research brief: {research_stage.get('brief_path') or '—'}\n"
                    f"Executor tried: `{executor}`\n",
                    encoding="utf-8",
                )
        else:
            # local_engineer loop: generate → test → repair
            repair = ""
            touched_all: list[str] = []
            last_attempt: dict[str, Any] = {}
            if not run_impl:
                impl.update(
                    {
                        "ok": True,
                        "mode": "deferred",
                        "note_ru": "run_impl=false — codegen пропущен (тест/dry-run).",
                    }
                )
            else:
                for attempt in range(1, max_test_attempts + 1):
                    attempt_res = run_local_engineer_once(
                        root=src,
                        task=task,
                        plan=plan,
                        related=related,
                        repair_feedback=repair,
                    )
                    impl["attempts"].append({"n": attempt, "result": attempt_res})
                    last_attempt = attempt_res
                    if attempt_res.get("cannot"):
                        break
                    touched_all.extend(attempt_res.get("touched") or [])
                    # validate mid-loop
                    cmds = list(stack.get("test_commands") or [])
                    if not cmds:
                        repair = ""
                        break
                    test_res = _run(cmds[0], cwd=src, timeout=300)
                    if test_res["ok"]:
                        repair = ""
                        break
                    repair = (
                        f"Tests failed (attempt {attempt}).\n"
                        f"stderr:\n{test_res.get('stderr') or ''}\n"
                        f"stdout:\n{test_res.get('stdout') or ''}"
                    )
                impl["files_touched"] = sorted(set(touched_all))
                impl["ok"] = bool(touched_all) and not last_attempt.get("cannot")
                impl["mode"] = "local_engineer"
                impl["summary"] = last_attempt.get("summary")
                impl["cannot_reason"] = last_attempt.get("cannot_reason")
                if last_attempt.get("cannot") and not touched_all:
                    impl["ok"] = False
                    impl["message_ru"] = (
                        f"Engineer отказался: {last_attempt.get('cannot_reason')}"
                    )

            (ws / "IMPLEMENTATION_STATUS.md").write_text(
                "# Implementation Status\n\n"
                f"Route: `{impl.get('mode')}`\n"
                f"Issue: {issue_url}\n"
                f"Branch: `{branch}`\n"
                f"Files: {', '.join(impl.get('files_touched') or []) or '—'}\n"
                f"Summary: {impl.get('summary') or impl.get('message_ru') or '—'}\n\n"
                "CEO Submit PR still required. Estimated ≠ REAL.\n",
                encoding="utf-8",
            )
            report["stages"]["implementation"] = impl

            # --- Stage 4: Validation (final) ---
            validation = {
                "ok": True,
                "attempts": [],
                "passed": None,
                "skipped": False,
            }
            cmds = list(stack.get("test_commands") or [])
            if not cmds:
                validation["skipped"] = True
                validation["reason"] = "no_test_command_detected"
                # Without tests, only accept if we have a patch
                validation["passed"] = bool(impl.get("files_touched"))
            else:
                res = _run(cmds[0], cwd=src, timeout=300)
                validation["attempts"].append({"n": "final", "result": res})
                validation["passed"] = bool(res["ok"])
            report["stages"]["validation"] = validation

            # Commit if we have changes (never push)
            if impl.get("files_touched"):
                # Keep factory commits clean — no bytecode noise
                for junk in src.rglob("__pycache__"):
                    shutil.rmtree(junk, ignore_errors=True)
                for junk in src.rglob("*.pyc"):
                    try:
                        junk.unlink()
                    except OSError:
                        pass
                _run([git, "add", "-A"], cwd=src, timeout=60)
                commit = _run(
                    [
                        git,
                        "-c",
                        "user.email=farm@virtus.local",
                        "-c",
                        "user.name=Virtus Farm Engine",
                        "commit",
                        "-m",
                        f"fix: {title[:60]} (Opire #{issue_id})",
                    ],
                    cwd=src,
                    timeout=60,
                )
                report["stages"]["commit"] = {
                    "ok": commit["ok"],
                    "result": commit,
                    "pushed": False,
                    "note_ru": "Commit локальный. Push/PR — только после CEO Submit.",
                }

        # If local engineer produced nothing useful — fail closed (not fake success)
        if (
            route.get("route") == "local_engineer"
            and run_impl
            and not (report["stages"].get("implementation") or {}).get("files_touched")
        ):
            report["ok"] = False
            report["stage"] = "failed"
            report["error"] = "implementation_empty"
            report["error_detail"] = (
                (report["stages"].get("implementation") or {}).get("message_ru")
                or (report["stages"].get("implementation") or {}).get("cannot_reason")
                or "Нет безопасного патча — Farm сказал «не могу» вместо ложного PR."
            )
            report["elapsed_sec"] = round(time.time() - started, 1)
            return report

        impl_final = report["stages"].get("implementation") or {}
        patch_ready = bool(impl_final.get("files_touched"))
        paused_external = (
            route.get("route") == "needs_external"
            and impl_final.get("mode") == "needs_external"
            and not patch_ready
        )

        # --- Stage 5: PR Intelligence ---
        body = build_pr_body(
            issue_url=issue_url,
            issue_id=issue_id,
            plan=plan,
            title=title,
        )
        # Enrich PR body with execution summary
        body = (
            body
            + f"\n## Execution\nRoute: {impl_final.get('mode')}\n"
            + f"Files: {', '.join(impl_final.get('files_touched') or []) or 'brief only'}\n"
            + f"{impl_final.get('summary') or impl_final.get('note_ru') or ''}\n"
        )
        pr_path = ws / "PULL_REQUEST.md"
        pr_path.write_text(body, encoding="utf-8")
        report["stages"]["pr_intelligence"] = {
            "ok": True,
            "draft": True,
            "title": f"fix: {title[:72]}",
            "body_path": str(pr_path),
            "body_preview": body[:1200],
            "opire_claim": f"/claim #{issue_id}" if issue_id else "/claim",
            "gh_hint": (
                f'gh pr create --draft --title "fix: ..." --body-file "{pr_path}"'
            ),
            "push_forbidden_until_ceo_submit": True,
            "patch_ready": patch_ready,
        }

        # --- Stage 6 hook ---
        report["stages"]["review_loop"] = {
            "ok": True,
            "armed": True,
            "note_ru": (
                "После CEO Submit: читать review comments → patch → tests → update PR."
            ),
        }

        report["ok"] = True
        report["workspace"] = str(ws)
        report["branch"] = branch
        report["elapsed_sec"] = round(time.time() - started, 1)
        report["patch_ready"] = patch_ready

        if paused_external:
            report["stage"] = "awaiting_external"
            report["ready_for_ceo"] = {
                "message_ru": (
                    "Impossible в авто-режиме: патч не получен. "
                    "Задача будет снята (Skip) — следующая bounty, без Cursor."
                ),
                "actions": ["skip"],
                "route": "needs_external",
                "patch_ready": False,
            }
            return report

        ready_msg = (
            "Draft PR package готов (код + /claim). Нажмите Отправить — "
            "push/PR только с вашего подтверждения."
            if patch_ready
            else "Пакет подготовлен, но патч пуст — не отправляйте на GitHub."
        )
        report["stage"] = "awaiting_ceo_submit"
        report["ready_for_ceo"] = {
            "message_ru": ready_msg,
            "actions": ["submit_pr", "skip"] if patch_ready else ["skip"],
            "route": route.get("route"),
            "patch_ready": patch_ready,
        }
        return report


def merge_execution_into_task(task: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    out = dict(task)
    out["execution"] = report
    out["updated_at"] = _now()
    if report.get("estimate"):
        out["execution_estimate"] = report["estimate"]

    impl = (report.get("stages") or {}).get("implementation") or {}
    research = (report.get("stages") or {}).get("research") or {}
    validation = (report.get("stages") or {}).get("validation") or {}
    commit = (report.get("stages") or {}).get("commit") or {}
    patch_ready = bool(report.get("patch_ready") or impl.get("files_touched"))

    def _mark(ids: set[str], *, done: bool) -> None:
        for step in out.get("execution_checklist") or []:
            if step.get("id") in ids:
                step["done"] = done

    if report.get("stage") == "awaiting_external" or (
        impl.get("mode") == "needs_external" and not patch_ready
    ):
        out["status"] = "needs_external"
        out["execution_error"] = None
        # Honest checklist — never mark implementation/validation/PR as done
        _mark({"repo_intel", "planning"}, done=True)
        _mark({"research"}, done=bool(research.get("ok")))
        _mark(
            {"implementation", "validation", "pr_intelligence", "ceo_submit", "review_loop"},
            done=False,
        )
    elif report.get("ok") and report.get("stage") == "awaiting_ceo_submit":
        out["status"] = "draft_pr"
        _mark({"repo_intel", "planning"}, done=True)
        _mark({"research"}, done=bool(research.get("ok")) or not research)
        _mark({"implementation"}, done=patch_ready)
        _mark(
            {"validation"},
            done=bool(validation.get("passed"))
            or (validation.get("skipped") and patch_ready),
        )
        _mark({"pr_intelligence"}, done=True)
        # commit step if present in checklist (optional id)
        if commit.get("ok"):
            _mark({"commit"}, done=True)
    elif report.get("stage") == "failed":
        out["status"] = "ceo_approved"
        out["execution_error"] = report.get("error_detail") or report.get("error")
    else:
        out["status"] = "executing"
    return out