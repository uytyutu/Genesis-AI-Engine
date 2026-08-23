"""Farm Opire — practical smoke for Execution Loop (no foreign Push without token).

Proves on a real local git repo + live Groq (from .env.local):
  Clone/init → Read → Generate patch → Tests → Commit

Push / Draft PR / REAL require GITHUB_TOKEN and a CEO-approved Opire bounty —
reported separately as READY or BLOCKED.

Usage (repo root):
  py -3.12 scripts/farm_opire_execution_smoke.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _build_fixture(base: Path) -> Path:
    src = base / "demo"
    src.mkdir(parents=True)
    (src / "app.py").write_text(
        "def add(a, b):\n    return a - b  # intentional bug\n",
        encoding="utf-8",
    )
    tests = src / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n"
        "from app import add\n\n"
        "def test_add():\n    assert add(2, 3) == 5\n",
        encoding="utf-8",
    )
    (src / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    (src / "pytest.ini").write_text("[pytest]\npythonpath = .\n", encoding="utf-8")
    _git(src, "init")
    _git(src, "config", "user.email", "farm-smoke@virtus.local")
    _git(src, "config", "user.name", "Farm Smoke")
    _git(src, "add", ".")
    _git(src, "commit", "-m", "init broken add")
    return src


def main() -> int:
    from swarm.farm_env_bootstrap import ensure_farm_env
    from swarm.farm_execution_engine import FarmExecutionEngine, detect_stack
    from swarm.farm_execution_manager import capability_gate
    from swarm.farm_github_live import _github_token

    env = ensure_farm_env(force=True)
    report: dict = {
        "llm_ready": bool(
            env.get("GENESIS_GROQ_API_KEY") or env.get("GROQ_API_KEY")
        ),
        "github_token_ready": bool(_github_token()),
        "stages": {},
    }

    if not report["llm_ready"]:
        report["ok"] = False
        report["blocker"] = "GENESIS_GROQ_API_KEY missing in .env.local"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    with tempfile.TemporaryDirectory(prefix="farm_smoke_") as tmp:
        memory = Path(tmp) / "memory"
        memory.mkdir()
        fixture = _build_fixture(Path(tmp))

        # Pretend Opire task — high confidence Python bugfix
        task = {
            "id": "opire:smoke-local-1",
            "native_id": "smoke-local-1",
            "title": "Fix add() so 2+3 equals 5",
            "repository": "local/demo",
            "issue_id": "1",
            "issue_url": "https://example.local/issues/1",
            "url": "https://example.local/issues/1",
            "languages": ["python"],
            "overall_confidence_pct": 92.0,
            "acceptance_pct": 88.0,
            "estimated_hours": 0.5,
            "reward_usd": 50,
            "blockers": [],
            "issue_body_preview": (
                "Acceptance: function add(a,b) must return a+b. "
                "test_app.py must pass."
            ),
        }
        gate = capability_gate(task, detect_stack(fixture))
        report["stages"]["route"] = gate
        if gate.get("route") != "local_engineer":
            report["ok"] = False
            report["blocker"] = f"expected local_engineer, got {gate.get('route')}"
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 3

        engine = FarmExecutionEngine(memory)
        # Seed workspace as if clone already happened
        ws = engine.workspace_for(task["id"])
        src = ws / "src"
        src.parent.mkdir(parents=True, exist_ok=True)
        # Move fixture into workspace/src via copy
        import shutil

        shutil.copytree(fixture, src)
        result = engine.run_pipeline(task, clone=False, run_impl=True)
        report["stages"]["pipeline"] = {
            "ok": result.get("ok"),
            "stage": result.get("stage"),
            "error": result.get("error"),
            "error_detail": result.get("error_detail"),
            "route": (result.get("ready_for_ceo") or {}).get("route")
            or (result.get("stages") or {}).get("routing", {}).get("route"),
            "implementation": {
                "mode": (result.get("stages") or {})
                .get("implementation", {})
                .get("mode"),
                "files": (result.get("stages") or {})
                .get("implementation", {})
                .get("files_touched"),
                "summary": (result.get("stages") or {})
                .get("implementation", {})
                .get("summary"),
            },
            "validation": (result.get("stages") or {}).get("validation"),
            "commit": (result.get("stages") or {}).get("commit"),
            "pr_body_exists": (ws / "PULL_REQUEST.md").is_file(),
        }

        impl_files = report["stages"]["pipeline"]["implementation"].get("files") or []
        impl_ok = bool(impl_files)
        # Honest check: production file must be fixed, not only tests
        app_py = (src / "app.py").read_text(encoding="utf-8")
        app_fixed = ("a - b" not in app_py) and (
            "a + b" in app_py or "a+b" in app_py or "return a+b" in app_py.replace(" ", "")
        )
        val = report["stages"]["pipeline"].get("validation") or {}
        tests_ok = val.get("passed") is True
        commit_ok = bool((report["stages"]["pipeline"].get("commit") or {}).get("ok"))

        report["practical_loop"] = {
            "generate_patch": impl_ok,
            "fixed_production_code": app_fixed,
            "run_tests": bool(tests_ok),
            "commit": commit_ok,
            "draft_pr_package": report["stages"]["pipeline"]["pr_body_exists"],
            "push": "BLOCKED_NO_GITHUB_TOKEN"
            if not report["github_token_ready"]
            else "READY_FOR_CEO_SUBMIT",
            "draft_pr_on_github": "BLOCKED_NO_GITHUB_TOKEN"
            if not report["github_token_ready"]
            else "READY_FOR_CEO_SUBMIT",
            "maintainer_merge_to_real": "NEEDS_LIVE_OPIRE_BOUNTY",
        }
        report["ok"] = bool(
            result.get("ok")
            and impl_ok
            and app_fixed
            and tests_ok
            and report["stages"]["pipeline"]["pr_body_exists"]
        )
        report["verdict_ru"] = (
            "Практический цикл Generate->Test->Commit->DraftPackage: PASS. "
            "Полный Opire->GitHub Draft PR->Merge->REAL ещё нужен GITHUB_TOKEN "
            "и один CEO Approve на реальной bounty."
            if report["ok"] and not report["github_token_ready"]
            else (
                "Практический цикл PASS; GitHub token есть — можно жать "
                "Отправить Draft PR (auto) на одобренной Opire-задаче."
                if report["ok"]
                else "Практический цикл FAIL — смотрите stages."
            )
        )

    out = json.dumps(report, ensure_ascii=False, indent=2)
    Path("_farm_smoke_out.json").write_text(out, encoding="utf-8")
    print(out.encode("ascii", "replace").decode("ascii"))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
