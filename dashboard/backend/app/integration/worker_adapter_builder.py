"""Worker Adapter Builder — factory for income sources with maturity levels.

Research Lab finds platforms. This module builds adapters and gates Work Farm entry.

Maturity (strict, Reality over Simulation):
  L0 Unknown
  L1 Candidate          — research OK, no adapter
  L2 Adapter written    — scaffold exists (not live execution)
  L3 Sandbox passed     — one dry-run test task OK (no claimed €)
  L4 First payout       — CONFIRMED real payout recorded by CEO
  L5 Working            — eligible for Work Farm (L2+L3+L4)
  L6 Scaled             — Working + volume / CEO mark

Forbidden:
  - auto-register / accept ToS / connect keys
  - promote Working without CONFIRMED payout
  - pretend sandbox dry-run is money
  - feed external tasks into Work Farm below L5
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BUILDER_VERSION = "worker_adapter_builder_v0"

MATURITY_LABELS: dict[int, str] = {
    0: "unknown",
    1: "candidate",
    2: "adapter_written",
    3: "sandbox_passed",
    4: "first_payout",
    5: "working",
    6: "scaled",
}

MATURITY_RU: dict[int, str] = {
    0: "Unknown",
    1: "Candidate",
    2: "Adapter written",
    3: "Sandbox passed",
    4: "First payout",
    5: "Working",
    6: "Scaled",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _utc_now()).isoformat()


class WorkerAdapterBuilder:
    def __init__(self, memory_dir: Path, lab: Any) -> None:
        self._memory = Path(memory_dir)
        self._lab = lab
        self._dir = self._memory / "worker_adapter_builder"
        self._adapters = self._dir / "adapters"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._adapters.mkdir(parents=True, exist_ok=True)
        self._state_path = self._dir / "state.json"
        self._sandbox_path = self._dir / "sandbox_runs.jsonl"

    def _load_state(self) -> dict[str, Any]:
        empty: dict[str, Any] = {
            "version": BUILDER_VERSION,
            "maturity": {},
            "adapters": {},
            "sandbox": {},
            "scaled_at": {},
        }
        if not self._state_path.is_file():
            self._save_state(empty)
            return empty
        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return empty
        if not isinstance(data, dict):
            return empty
        data.setdefault("maturity", {})
        data.setdefault("adapters", {})
        data.setdefault("sandbox", {})
        data.setdefault("scaled_at", {})
        return data

    def _save_state(self, state: dict[str, Any]) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _set_level(self, state: dict[str, Any], platform_id: str, level: int) -> None:
        cur = int((state["maturity"].get(platform_id) or {}).get("level") or 0)
        level = max(0, min(6, int(level)))
        # Never decrease except explicit reset (not exposed)
        if level < cur and cur >= 5 and level < 5:
            # allow staying; do not demote Working silently
            level = cur
        if level < cur:
            level = cur
        state["maturity"][platform_id] = {
            "level": level,
            "label": MATURITY_LABELS[level],
            "label_ru": MATURITY_RU[level],
            "updated_at": _iso(),
        }

    def sync_from_lab(self) -> dict[str, Any]:
        """Align maturity with Research Lab catalog. Does not invent payouts."""
        state = self._load_state()
        board = self._lab.board()
        for plat in board.get("platforms") or []:
            if not isinstance(plat, dict):
                continue
            pid = str(plat.get("id") or "")
            if not pid:
                continue
            verdict = str(plat.get("verdict") or "")
            cur = int((state["maturity"].get(pid) or {}).get("level") or 0)

            if verdict == "reject":
                state["maturity"][pid] = {
                    "level": 0,
                    "label": "unknown",
                    "label_ru": "Rejected / Unknown",
                    "updated_at": _iso(),
                    "rejected": True,
                }
                continue

            # Bootstrap Path A as proven Working (own Stripe cycle)
            if pid == "path_a_stripe" and plat.get("real_payout_proven"):
                if cur < 5:
                    self._set_level(state, pid, 5)
                if pid not in state["adapters"]:
                    self._write_scaffold(state, pid, plat, auto=True)
                continue

            if cur >= 2:
                continue  # keep adapter progress
            if verdict in ("candidate", "partial", "working"):
                self._set_level(state, pid, max(cur, 1))
            elif cur == 0:
                self._set_level(state, pid, 0)

            # If payout already proven in lab but not yet L4+
            if plat.get("real_payout_proven") and cur >= 3:
                self._set_level(state, pid, max(cur, 4))
            elif plat.get("real_payout_proven") and cur < 3:
                # payout without sandbox — stay honest: note only
                mat = state["maturity"].setdefault(pid, {})
                mat["payout_before_sandbox"] = True

        self._save_state(state)
        return {"ok": True, "maturity": state["maturity"]}

    def _write_scaffold(
        self, state: dict[str, Any], platform_id: str, plat: dict[str, Any], *, auto: bool = False
    ) -> dict[str, Any]:
        path = self._adapters / f"{platform_id}.json"
        scaffold = {
            "platform_id": platform_id,
            "name": plat.get("name"),
            "version": "adapter_scaffold_v0",
            "created_at": _iso(),
            "live_execution": False,
            "sandbox_only": True,
            "work_farm_eligible": False,
            "capabilities": {
                "get_task": bool(plat.get("api_get_task")),
                "submit_result": bool(plat.get("api_submit_result")),
                "receive_payout": bool(plat.get("api_receive_payout")),
            },
            "hooks": {
                "get_task": None,
                "submit_result": None,
                "check_payout": None,
            },
            "rule_ru": (
                "Scaffold only. Live fetch/submit disabled until L5 Working "
                "and CEO wires real hooks. Sandbox never claims money."
            ),
            "auto_bootstrap": auto,
        }
        path.write_text(json.dumps(scaffold, ensure_ascii=False, indent=2), encoding="utf-8")
        state["adapters"][platform_id] = {
            "path": str(path.relative_to(self._memory)).replace("\\", "/"),
            "created_at": scaffold["created_at"],
            "live_execution": False,
        }
        return scaffold

    def create_adapter(self, platform_id: str, *, note: str = "") -> dict[str, Any]:
        """L1 → L2: write adapter scaffold. Requires CEO approve (except path_a)."""
        self.sync_from_lab()
        state = self._load_state()
        pid = (platform_id or "").strip()
        lab_state = self._lab._load_state()  # noqa: SLF001 — shared memory catalog
        plat = (lab_state.get("platforms") or {}).get(pid)
        if not isinstance(plat, dict):
            return {"ok": False, "error": "platform_not_found"}
        if plat.get("verdict") == "reject":
            return {"ok": False, "error": "rejected_platform"}
        approvals = lab_state.get("ceo_approvals") or {}
        if pid != "path_a_stripe" and pid not in approvals and not plat.get("ceo_approved"):
            return {
                "ok": False,
                "error": "ceo_approve_required",
                "detail_ru": "Сначала CEO approve в Research Lab (ключ/ToS вручную).",
            }
        scaffold = self._write_scaffold(state, pid, plat)
        if note:
            scaffold["ceo_note"] = note[:500]
            path = self._adapters / f"{pid}.json"
            path.write_text(json.dumps(scaffold, ensure_ascii=False, indent=2), encoding="utf-8")
        self._set_level(state, pid, 2)
        self._save_state(state)
        return {
            "ok": True,
            "platform_id": pid,
            "maturity_level": 2,
            "maturity_label": MATURITY_RU[2],
            "adapter": scaffold,
            "message_ru": (
                "Adapter scaffold создан (L2). Дальше: Sandbox → одна тестовая задача "
                "→ CONFIRMED payout → Working. Live execution ещё выключен."
            ),
        }

    def run_sandbox(self, platform_id: str) -> dict[str, Any]:
        """L2 → L3: one dry-run test task. Never claims payout / never hits live worker APIs."""
        self.sync_from_lab()
        state = self._load_state()
        pid = (platform_id or "").strip()
        level = int((state["maturity"].get(pid) or {}).get("level") or 0)
        if level < 2 and pid not in state["adapters"]:
            return {"ok": False, "error": "adapter_required", "detail_ru": "Сначала Create Adapter (L2)."}
        if pid not in state["adapters"]:
            return {"ok": False, "error": "adapter_missing"}

        # Dry-run: structural test only — Reality: no €, no live platform call
        result = {
            "platform_id": pid,
            "mode": "dry_run",
            "task_id": f"sandbox-{pid}-{_utc_now().strftime('%Y%m%d%H%M%S')}",
            "steps": [
                {"step": "get_task", "ok": True, "note": "simulated — live API not called"},
                {"step": "execute", "ok": True, "note": "local dry-run stub"},
                {"step": "submit_result", "ok": True, "note": "simulated — not sent to platform"},
                {
                    "step": "payout_check",
                    "ok": False,
                    "note": "Sandbox never claims payout — need real CONFIRMED proof for L4",
                },
            ],
            "passed": True,
            "money_claimed_eur": 0,
            "at": _iso(),
        }
        with self._sandbox_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(result, ensure_ascii=False) + "\n")
        state["sandbox"][pid] = {
            "last_run_at": result["at"],
            "passed": True,
            "task_id": result["task_id"],
            "money_claimed_eur": 0,
        }
        self._set_level(state, pid, 3)
        self._save_state(state)
        return {
            "ok": True,
            "platform_id": pid,
            "maturity_level": 3,
            "maturity_label": MATURITY_RU[3],
            "sandbox": result,
            "message_ru": (
                "Sandbox passed (L3). Выплаты нет — это правильно. "
                "Запиши реальную выплату (payout-proof) → L4, затем Promote Working → L5."
            ),
        }

    def on_payout_recorded(self, platform_id: str) -> dict[str, Any]:
        """Called after Lab CONFIRMED payout — raise to L4 (not L5 yet)."""
        state = self._load_state()
        pid = (platform_id or "").strip()
        level = int((state["maturity"].get(pid) or {}).get("level") or 0)
        if level < 3:
            self._set_level(state, pid, max(level, 1))
            mat = state["maturity"][pid]
            mat["payout_before_sandbox"] = True
            mat["gate_ru"] = "Выплата записана, но Sandbox (L3) ещё не пройден — Working запрещён."
            self._save_state(state)
            return {
                "ok": True,
                "platform_id": pid,
                "maturity_level": int(mat["level"]),
                "blocked_from_working": True,
                "message_ru": mat["gate_ru"],
            }
        self._set_level(state, pid, 4)
        self._save_state(state)
        return {
            "ok": True,
            "platform_id": pid,
            "maturity_level": 4,
            "maturity_label": MATURITY_RU[4],
            "message_ru": "First payout зафиксирован (L4). Вызови Promote Working для L5.",
        }

    def promote_working(self, platform_id: str) -> dict[str, Any]:
        """L4 → L5 only if adapter + sandbox + CONFIRMED payout."""
        self.sync_from_lab()
        state = self._load_state()
        pid = (platform_id or "").strip()
        level = int((state["maturity"].get(pid) or {}).get("level") or 0)
        lab_state = self._lab._load_state()  # noqa: SLF001
        plat = (lab_state.get("platforms") or {}).get(pid) or {}
        proven = bool(plat.get("real_payout_proven")) or pid in self._lab._payout_ids()  # noqa: SLF001
        sand = state["sandbox"].get(pid) or {}
        has_adapter = pid in state["adapters"]

        missing = []
        if not has_adapter:
            missing.append("adapter (L2)")
        if not sand.get("passed"):
            missing.append("sandbox (L3)")
        if not proven:
            missing.append("CONFIRMED payout (L4)")
        if missing:
            return {
                "ok": False,
                "error": "maturity_gate",
                "missing": missing,
                "detail_ru": "Working только после: Adapter + Sandbox + первая реальная выплата.",
            }
        if level < 4 and proven and sand.get("passed") and has_adapter:
            self._set_level(state, pid, 4)
            level = 4

        self._set_level(state, pid, 5)
        # Mark scaffold eligible; live hooks still off until CEO wires them
        adapter_path = self._adapters / f"{pid}.json"
        if adapter_path.is_file():
            try:
                sc = json.loads(adapter_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                sc = {}
            sc["work_farm_eligible"] = True
            sc["live_execution"] = False  # still no auto-fetch until scaled hooks
            sc["promoted_working_at"] = _iso()
            adapter_path.write_text(json.dumps(sc, ensure_ascii=False, indent=2), encoding="utf-8")

        # Sync Lab verdict
        if isinstance(plat, dict) and plat.get("verdict") != "reject":
            plat = dict(plat)
            plat["verdict"] = "working"
            plat["maturity_level"] = 5
            lab_state["platforms"][pid] = plat
            self._lab._save_state(lab_state)  # noqa: SLF001

        self._save_state(state)
        return {
            "ok": True,
            "platform_id": pid,
            "maturity_level": 5,
            "maturity_label": MATURITY_RU[5],
            "work_farm_eligible": True,
            "live_execution": False,
            "message_ru": (
                "L5 Working: платформа может войти в Work Farm allowlist. "
                "Live auto-fetch задач всё ещё выключен — CEO подключает hooks отдельно. "
                "Ядро не нарушено."
            ),
        }

    def mark_scaled(self, platform_id: str, *, jobs_done: int = 0) -> dict[str, Any]:
        state = self._load_state()
        pid = (platform_id or "").strip()
        level = int((state["maturity"].get(pid) or {}).get("level") or 0)
        if level < 5:
            return {"ok": False, "error": "working_required"}
        self._set_level(state, pid, 6)
        state["scaled_at"][pid] = {"at": _iso(), "jobs_done": int(jobs_done or 0)}
        self._save_state(state)
        return {"ok": True, "platform_id": pid, "maturity_level": 6, "maturity_label": MATURITY_RU[6]}

    def work_farm_allowlist(self) -> list[str]:
        """Only L5+ platforms — Work Farm must not pull below this."""
        self.sync_from_lab()
        state = self._load_state()
        out = []
        for pid, mat in (state.get("maturity") or {}).items():
            if int((mat or {}).get("level") or 0) >= 5:
                out.append(pid)
        return sorted(out)

    def board(self) -> dict[str, Any]:
        self.sync_from_lab()
        state = self._load_state()
        lab = self._lab.board()
        rows = []
        for plat in lab.get("platforms") or []:
            if not isinstance(plat, dict):
                continue
            pid = str(plat.get("id") or "")
            mat = state["maturity"].get(pid) or {"level": 0, "label": "unknown", "label_ru": "Unknown"}
            level = int(mat.get("level") or 0)
            rows.append(
                {
                    **plat,
                    "maturity_level": level,
                    "maturity_label": mat.get("label") or MATURITY_LABELS.get(level, "unknown"),
                    "maturity_label_ru": mat.get("label_ru") or MATURITY_RU.get(level, "Unknown"),
                    "has_adapter": pid in state["adapters"],
                    "sandbox_passed": bool((state["sandbox"].get(pid) or {}).get("passed")),
                    "work_farm_eligible": level >= 5,
                    "live_execution": False,
                }
            )
        rows.sort(key=lambda r: (-int(r.get("maturity_level") or 0), -int(r.get("stars") or 0)))
        by_level = {str(i): 0 for i in range(7)}
        for r in rows:
            by_level[str(int(r.get("maturity_level") or 0))] += 1
        return {
            "ok": True,
            "version": BUILDER_VERSION,
            "title_ru": "Worker Adapter Builder",
            "rule_ru": (
                "Research → Create Adapter → Sandbox → First payout → Working → Scaled. "
                "Working без CONFIRMED payout запрещён. Live fetch ниже L5 запрещён."
            ),
            "levels_ru": [f"L{i} {MATURITY_RU[i]}" for i in range(7)],
            "pipeline_ru": [
                "Worker Research Lab",
                "CEO approve + key",
                "Create Adapter (L2)",
                "Sandbox one task (L3)",
                "First payout (L4)",
                "Working → Work Farm (L5)",
                "Scaled (L6)",
            ],
            "counts_by_level": by_level,
            "work_farm_allowlist": self.work_farm_allowlist(),
            "platforms": rows,
            "lab_findings": lab.get("findings") or [],
            "forbidden_ru": [
                "Working без Adapter + Sandbox + payout",
                "Sandbox ≠ деньги",
                "Авто-регистрация / ToS / ключи",
                "External tasks в Work Farm ниже L5",
            ],
        }
