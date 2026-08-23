"""Worker Research Lab — research platforms where official cycle is:

  get task → do work (API / allowed automation) → get paid

NOT: scrape "APIs that pay €0.01".
NOT: auto-register / accept ToS / connect accounts (CEO only).
NOT: Toloka Requester-as-worker (wrong API role).

Working status requires BOTH:
  1) ToS/API allow worker automation (documented)
  2) at least one CONFIRMED real payout recorded for that platform

Scan cadence: every 6 hours (state-driven; also manual POST /scan).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

LAB_VERSION = "worker_research_lab_v0"
SCAN_INTERVAL_HOURS = 6

# Research catalog — honest verdicts (not marketing). Update via scan/CEO.
_PLATFORM_SEED: list[dict[str, Any]] = [
    {
        "id": "toloka_requester",
        "name": "Toloka (Requester API)",
        "verdict": "reject",
        "stars": 1,
        "api_get_task": False,
        "api_submit_result": False,
        "api_receive_payout": False,
        "automation_pct": 0,
        "tos_automation": "forbidden_for_this_role",
        "reason_ru": (
            "Подключён Requester API — создавать задания, не брать себе на выполнение. "
            "Не подходит под Worker Farm."
        ),
        "next_ru": "Не добавлять в Work Farm как источник задач.",
    },
    {
        "id": "scale_ai_requester",
        "name": "Scale AI",
        "verdict": "reject",
        "stars": 1,
        "api_get_task": False,
        "api_submit_result": False,
        "api_receive_payout": False,
        "automation_pct": 0,
        "tos_automation": "requester_only",
        "reason_ru": "Requester / labeling customer API — Virtus платит, не получает работу.",
        "next_ru": "Оставить как cost/probe, не как worker source.",
    },
    {
        "id": "upwork",
        "name": "Upwork",
        "verdict": "reject",
        "stars": 1,
        "api_get_task": False,
        "api_submit_result": False,
        "api_receive_payout": False,
        "automation_pct": 5,
        "tos_automation": "typically_forbidden",
        "reason_ru": "Авто-заявки / бот-выполнение проектов обычно запрещены ToS.",
        "next_ru": "Только ручной CEO, не Worker Adapter.",
    },
    {
        "id": "fiverr",
        "name": "Fiverr",
        "verdict": "reject",
        "stars": 1,
        "api_get_task": False,
        "api_submit_result": False,
        "api_receive_payout": False,
        "automation_pct": 5,
        "tos_automation": "typically_forbidden",
        "reason_ru": "Похожие ограничения на автоматизацию заказов/предложений.",
        "next_ru": "Не строить адаптер без явного ToS green-light + payout proof.",
    },
    {
        "id": "amazon_mturk_worker",
        "name": "Amazon Mechanical Turk (Worker)",
        "verdict": "candidate",
        "stars": 4,
        "api_get_task": True,
        "api_submit_result": True,
        "api_receive_payout": True,
        "automation_pct": 70,
        "tos_automation": "restricted_review_required",
        "reason_ru": (
            "Официальный Worker API: HITs → submit → payout. "
            "Нужна проверка актуального ToS и аккаунт worker (CEO)."
        ),
        "next_ru": "CEO: изучить ToS + ключ → пробная выплата → тогда Working.",
    },
    {
        "id": "clickworker",
        "name": "Clickworker",
        "verdict": "candidate",
        "stars": 3,
        "api_get_task": True,
        "api_submit_result": True,
        "api_receive_payout": True,
        "automation_pct": 55,
        "tos_automation": "needs_review",
        "reason_ru": "Есть API-контуры для исполнителей; автоматизация и ToS — проверить перед адаптером.",
        "next_ru": "Research card: нужен CEO review ToS + ключ.",
    },
    {
        "id": "textbroker",
        "name": "Textbroker / content markets",
        "verdict": "candidate",
        "stars": 3,
        "api_get_task": True,
        "api_submit_result": True,
        "api_receive_payout": True,
        "automation_pct": 50,
        "tos_automation": "needs_review",
        "reason_ru": "Цикл заказ→текст→оплата возможен; AI-автоматизация часто ограничена правилами.",
        "next_ru": "Сопоставить с Content Farm SKU (свои клиенты) vs внешний рынок.",
    },
    {
        "id": "rapidapi_provider",
        "name": "RapidAPI (as API seller)",
        "verdict": "candidate",
        "stars": 4,
        "api_get_task": False,
        "api_submit_result": False,
        "api_receive_payout": True,
        "automation_pct": 90,
        "tos_automation": "allowed_as_seller",
        "env_key": "RAPIDAPI_KEY",
        "reason_ru": (
            "Не биржа задач: клиенты вызывают ваш API → выплата провайдеру. "
            "Близко к Commercial API Virtus (Audit), не к Toloka-worker."
        ),
        "next_ru": (
            "Ключ RAPIDAPI_KEY — в env. Candidate: не строить Worker Adapter до "
            "решения CEO (seller API vs worker). Усилить API Products при Approve."
        ),
    },
    {
        "id": "orbofi_experimental",
        "name": "Orbofi (AI agents / tokens)",
        "verdict": "candidate",
        "stars": 2,
        "api_get_task": False,
        "api_submit_result": False,
        "api_receive_payout": False,
        "automation_pct": 20,
        "tos_automation": "needs_review",
        "env_key": "ORBOFI_KEY",
        "experimental": True,
        "reason_ru": (
            "Experimental — не смешивать с ядром Virtus Core / Work Farm. "
            "Доход только если агент реально используется в экосистеме Orbofi; "
            "ключ ≠ автозаработок. 100 стартовых монет — бонус платформы, не прибыль."
        ),
        "next_ru": (
            "Research Lab → Orbofi Integration (Experimental). Сначала 3 проверки: "
            "(1) какие функции даёт API; (2) можно ли создавать/публиковать агентов; "
            "(3) есть ли статистика и начисления. Без PASS — не строить бизнес-модель."
        ),
    },
    {
        "id": "orbofi_experimental",
        "name": "Orbofi (AI agents / tokens)",
        "verdict": "candidate",
        "stars": 2,
        "api_get_task": False,
        "api_submit_result": False,
        "api_receive_payout": False,
        "automation_pct": 20,
        "tos_automation": "needs_review",
        "env_key": "ORBOFI_KEY",
        "experimental": True,
        "reason_ru": (
            "Experimental — не смешивать с ядром Virtus Core / Work Farm. "
            "Доход только если агент реально используется в экосистеме Orbofi; "
            "ключ ≠ автозаработок. 100 стартовых монет — бонус платформы, не прибыль."
        ),
        "next_ru": (
            "Research Lab → Orbofi Integration (Experimental). Сначала 3 проверки: "
            "(1) какие функции даёт API; (2) можно ли создавать/публиковать агентов; "
            "(3) есть ли статистика и начисления. Без PASS — не строить бизнес-модель."
        ),
    },
    {
        "id": "digistore_affiliate",
        "name": "Digistore24 Affiliate",
        "verdict": "partial",
        "stars": 4,
        "api_get_task": False,
        "api_submit_result": False,
        "api_receive_payout": True,
        "automation_pct": 40,
        "tos_automation": "affiliate_ok_need_sync",
        "reason_ru": (
            "Не get-task: рекомендация → покупка → комиссия. "
            "Ключ может быть; Ledger sync после CONFIRMED комиссии."
        ),
        "next_ru": "Affiliate Farm: webhook/listCommissions → Ledger.",
    },
    {
        "id": "path_a_stripe",
        "name": "Virtus Path A (own Stripe orders)",
        "verdict": "working",
        "stars": 5,
        "api_get_task": True,
        "api_submit_result": True,
        "api_receive_payout": True,
        "automation_pct": 95,
        "tos_automation": "own_platform",
        "reason_ru": (
            "Свой цикл: лид → КП → Stripe → Work Farm → Delivered. "
            "Единственный proven CONFIRMED € контур сегодня."
        ),
        "next_ru": "Масштабировать Ready→pay; не путать с внешними биржами.",
        "real_payout_proven": True,
    },
]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _utc_now()).isoformat()


def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


class WorkerResearchLab:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)
        self._dir = self._memory / "worker_research_lab"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._state_path = self._dir / "state.json"
        self._payouts_path = self._dir / "payout_proofs.jsonl"

    def _load_state(self) -> dict[str, Any]:
        empty = {
            "version": LAB_VERSION,
            "platforms": {p["id"]: dict(p) for p in _PLATFORM_SEED},
            "ceo_approvals": {},
            "last_scan_at": None,
            "next_scan_at": None,
            "scan_count": 0,
            "findings": [],
        }
        if not self._state_path.is_file():
            empty["next_scan_at"] = _iso(_utc_now())
            self._save_state(empty)
            return empty
        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return empty
        if not isinstance(data, dict):
            return empty
        platforms = data.get("platforms") if isinstance(data.get("platforms"), dict) else {}
        # Merge new seed platforms without wiping CEO fields
        for seed in _PLATFORM_SEED:
            pid = seed["id"]
            if pid not in platforms:
                platforms[pid] = dict(seed)
            else:
                # Keep CEO overrides; refresh research fields if not working
                cur = platforms[pid] if isinstance(platforms[pid], dict) else {}
                if cur.get("verdict") != "working":
                    for k, v in seed.items():
                        if k not in ("real_payout_proven",):
                            cur.setdefault(k, v)
                    platforms[pid] = cur
        data["platforms"] = platforms
        data.setdefault("ceo_approvals", {})
        data.setdefault("findings", [])
        data.setdefault("scan_count", 0)
        return data

    def _save_state(self, state: dict[str, Any]) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _payout_ids(self) -> set[str]:
        out: set[str] = set()
        if not self._payouts_path.is_file():
            return out
        try:
            for line in self._payouts_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict) and row.get("platform_id"):
                    out.add(str(row["platform_id"]))
        except OSError:
            pass
        return out

    def _recompute_working(self, plat: dict[str, Any], payouts: set[str]) -> dict[str, Any]:
        """Working only if ToS/API allow AND real payout proven."""
        pid = str(plat.get("id") or "")
        proven = bool(plat.get("real_payout_proven")) or pid in payouts
        plat["real_payout_proven"] = proven
        cycle_ok = bool(plat.get("api_get_task")) and bool(plat.get("api_submit_result")) and bool(
            plat.get("api_receive_payout")
        )
        # Seller / affiliate / own path exceptions
        if pid in ("rapidapi_provider", "digistore_affiliate", "path_a_stripe"):
            cycle_ok = bool(plat.get("api_receive_payout"))
        tos = str(plat.get("tos_automation") or "")
        tos_ok = tos in (
            "allowed",
            "allowed_as_seller",
            "own_platform",
            "affiliate_ok_need_sync",
            "restricted_review_required",  # candidate until CEO
        )
        if plat.get("verdict") == "reject":
            return plat
        # Auto-Working only for own Path A. External → Adapter Builder L5 promote.
        if proven and pid == "path_a_stripe":
            plat["verdict"] = "working"
        elif proven and tos == "own_platform" and cycle_ok:
            plat["verdict"] = "working"
        elif cycle_ok and tos_ok and not proven:
            if plat.get("verdict") not in ("reject", "working"):
                plat["verdict"] = "candidate"
                plat["gate_ru"] = (
                    "Правила/API выглядят ок, но нет CONFIRMED payout proof — Working запрещён."
                )
        elif proven and plat.get("verdict") != "working":
            if plat.get("verdict") not in ("reject",):
                plat["verdict"] = "candidate"
                plat["gate_ru"] = (
                    "Payout есть — нужен Adapter Builder: Sandbox (L3) → Promote Working (L5)."
                )
        return plat

    def maybe_scan(self, *, force: bool = False) -> dict[str, Any]:
        state = self._load_state()
        now = _utc_now()
        next_at = _parse_dt(str(state.get("next_scan_at") or ""))
        if not force and next_at and now < next_at:
            return {
                "ok": True,
                "scanned": False,
                "next_scan_at": state.get("next_scan_at"),
                "reason": "not_due",
            }
        return self.scan(persist=True)

    def scan(self, *, persist: bool = True) -> dict[str, Any]:
        """Re-evaluate catalog; emit findings for CEO. Does not register accounts."""
        state = self._load_state()
        payouts = self._payout_ids()
        findings: list[dict[str, Any]] = []
        now = _iso()

        for pid, plat in list(state["platforms"].items()):
            if not isinstance(plat, dict):
                continue
            plat = self._recompute_working(dict(plat), payouts)
            plat["id"] = pid
            state["platforms"][pid] = plat

            if plat.get("verdict") == "reject":
                continue
            if plat.get("verdict") == "working":
                findings.append(
                    {
                        "id": f"find-{pid}-working",
                        "platform_id": pid,
                        "name": plat.get("name"),
                        "stars": plat.get("stars"),
                        "verdict": "working",
                        "title_ru": f"{plat.get('name')}: Working (цикл доказан)",
                        "detail_ru": plat.get("reason_ru"),
                        "needs_ceo_key": False,
                        "can_get_task": plat.get("api_get_task"),
                        "can_submit": plat.get("api_submit_result"),
                        "can_payout": plat.get("api_receive_payout"),
                        "at": now,
                    }
                )
            elif plat.get("verdict") in ("candidate", "partial"):
                findings.append(
                    {
                        "id": f"find-{pid}-candidate",
                        "platform_id": pid,
                        "name": plat.get("name"),
                        "stars": plat.get("stars"),
                        "verdict": plat.get("verdict"),
                        "title_ru": f"{plat.get('name')}: кандидат в Worker Adapter",
                        "detail_ru": plat.get("reason_ru"),
                        "needs_ceo_key": True,
                        "can_get_task": plat.get("api_get_task"),
                        "can_submit": plat.get("api_submit_result"),
                        "can_payout": plat.get("api_receive_payout"),
                        "gate_ru": plat.get("gate_ru")
                        or "CEO: ToS + ключ + одна реальная выплата → Working.",
                        "next_ru": plat.get("next_ru"),
                        "at": now,
                    }
                )

        findings.sort(key=lambda f: (-int(f.get("stars") or 0), str(f.get("verdict"))))
        state["findings"] = findings[:40]
        state["last_scan_at"] = now
        state["next_scan_at"] = _iso(_utc_now() + timedelta(hours=SCAN_INTERVAL_HOURS))
        state["scan_count"] = int(state.get("scan_count") or 0) + 1
        if persist:
            self._save_state(state)
        return {
            "ok": True,
            "scanned": True,
            "scan_count": state["scan_count"],
            "last_scan_at": state["last_scan_at"],
            "next_scan_at": state["next_scan_at"],
            "findings_count": len(findings),
            "findings": findings,
        }

    def ceo_approve(self, platform_id: str, *, note: str = "") -> dict[str, Any]:
        """CEO marks platform for adapter queue — does NOT connect keys or accept ToS."""
        state = self._load_state()
        pid = (platform_id or "").strip()
        plat = state["platforms"].get(pid)
        if not isinstance(plat, dict):
            return {"ok": False, "error": "platform_not_found"}
        if plat.get("verdict") == "reject":
            return {"ok": False, "error": "rejected_platform", "detail_ru": plat.get("reason_ru")}
        state["ceo_approvals"][pid] = {
            "approved_at": _iso(),
            "note": (note or "").strip()[:500],
            "status": "approved_awaiting_key_and_payout",
        }
        plat["ceo_approved"] = True
        state["platforms"][pid] = plat
        self._save_state(state)
        return {
            "ok": True,
            "platform_id": pid,
            "message_ru": (
                "Одобрено для очереди Worker Adapter. "
                "Регистрация / ToS / ключ — только вручную CEO. "
                "Working — только после CONFIRMED payout."
            ),
            "approval": state["ceo_approvals"][pid],
        }

    def record_payout_proof(
        self,
        platform_id: str,
        *,
        amount_eur: float,
        reference: str = "",
        note: str = "",
    ) -> dict[str, Any]:
        """CEO records one real payout — required gate to Working."""
        state = self._load_state()
        pid = (platform_id or "").strip()
        if pid not in state["platforms"]:
            return {"ok": False, "error": "platform_not_found"}
        amount = round(float(amount_eur or 0), 2)
        if amount <= 0:
            return {"ok": False, "error": "amount_required"}
        row = {
            "platform_id": pid,
            "amount_eur": amount,
            "reference": (reference or "").strip()[:200],
            "note": (note or "").strip()[:500],
            "at": _iso(),
            "confidence": "CONFIRMED",
        }
        with self._payouts_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        plat = dict(state["platforms"][pid])
        plat["real_payout_proven"] = True
        # Path A may stay/become working; external platforms need Adapter Builder L5
        if pid == "path_a_stripe" or plat.get("tos_automation") == "own_platform":
            plat["verdict"] = "working"
        elif plat.get("verdict") == "working" and pid != "path_a_stripe":
            # Do not keep working without builder promote — demote to candidate until L5
            plat["verdict"] = "candidate"
            plat["gate_ru"] = (
                "Payout записан (L4 path). Working только через Adapter Builder Promote (L5)."
            )
        state["platforms"][pid] = plat
        self._save_state(state)
        self.scan(persist=True)
        return {"ok": True, "proof": row, "platform": state["platforms"][pid]}

    def attach_maturity(self, platforms: list[dict[str, Any]], maturity_map: dict[str, Any]) -> list[dict[str, Any]]:
        out = []
        for p in platforms:
            pid = str(p.get("id") or "")
            mat = maturity_map.get(pid) or {}
            level = int(mat.get("level") or (5 if p.get("verdict") == "working" and pid == "path_a_stripe" else (1 if p.get("verdict") in ("candidate", "partial") else 0)))
            row = dict(p)
            row["maturity_level"] = level
            row["maturity_label"] = mat.get("label") or ("working" if level >= 5 else "candidate" if level >= 1 else "unknown")
            out.append(row)
        return out

    def board(self) -> dict[str, Any]:
        self.maybe_scan(force=False)
        state = self._load_state()
        platforms = list((state.get("platforms") or {}).values())
        platforms = [p for p in platforms if isinstance(p, dict)]
        for p in platforms:
            env_name = str(p.get("env_key") or "").strip()
            if env_name:
                p["env_key_present"] = bool(os.getenv(env_name, "").strip())
            elif str(p.get("id") or "") == "rapidapi_provider":
                p["env_key"] = "RAPIDAPI_KEY"
                p["env_key_present"] = bool(os.getenv("RAPIDAPI_KEY", "").strip())
        platforms.sort(key=lambda p: (-int(p.get("stars") or 0), str(p.get("name"))))
        working = [p for p in platforms if p.get("verdict") == "working"]
        candidates = [p for p in platforms if p.get("verdict") in ("candidate", "partial")]
        rejected = [p for p in platforms if p.get("verdict") == "reject"]
        return {
            "ok": True,
            "version": LAB_VERSION,
            "title_ru": "Worker Research Lab",
            "rule_ru": (
                "Новая платформа = Working только если правила разрешают автоматизацию "
                "И есть хотя бы одна реальная выплата. "
                "Регистрация / ToS / ключи — только CEO. "
                "Adapter Builder: L0→L6 до входа в Work Farm."
            ),
            "scan_interval_hours": SCAN_INTERVAL_HOURS,
            "last_scan_at": state.get("last_scan_at"),
            "next_scan_at": state.get("next_scan_at"),
            "scan_count": state.get("scan_count"),
            "counts": {
                "working": len(working),
                "candidates": len(candidates),
                "rejected": len(rejected),
                "findings": len(state.get("findings") or []),
            },
            "findings": state.get("findings") or [],
            "platforms": platforms,
            "ceo_approvals": state.get("ceo_approvals") or {},
            "pipeline_ru": [
                "Internet / catalogs",
                "Worker Research",
                "CEO key + ToS",
                "Adapter Builder L2–L5",
                "Work Farm",
                "Quality",
                "Revenue",
                "Ledger",
            ],
            "forbidden_ru": [
                "Авто-регистрация аккаунтов",
                "Авто-принятие ToS",
                "Подключение ключей без CEO",
                "Working без CONFIRMED payout",
                "Work Farm ниже maturity L5",
            ],
        }
