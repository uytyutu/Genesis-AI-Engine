"""Farm Market Scanner — continuous monitor of legal Earn markets.

Two projects inside Virtus (do not merge):
  1) Commercial Engine — Places → Lead → Email → Stripe → REAL (works with buyers)
  2) Farm Engine — Internet → Scanner → ToS/Automation/API → Earn Connector
     → jobs → External Payout → REAL (this loop; market may be empty)

Honest empty state is a feature:
  «Сегодня подходящих Earn-платформ не найдено.»

Finance Reality Law: facts first; Scanner never invents REAL.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DIGEST_FILE = "farm_market_scanner_digest.json"

# Extra known platforms for daily monitor (beyond farm_engine seed catalog).
_MONITOR_EXTRA: tuple[dict[str, Any], ...] = (
    {
        "id": "platform-mturk",
        "title": "Amazon MTurk",
        "track": "reject",
        "first_payout_score": 0,
        "autonomy_score": 0,
        "opinion_ru": "Human microtasks / ToS — Reject.",
        "automation_officially_allowed": False,
        "has_api": True,
        "pays_providers": True,
        "no_forbidden_human_judgment": False,
        "evidence_status": "hard_reject",
        "hard_reject": True,
        "opportunity_id": "reject-mturk-performer-bot",
    },
    {
        "id": "platform-outlier",
        "title": "Outlier (and similar AI labeling)",
        "track": "reject",
        "first_payout_score": 0,
        "autonomy_score": 0,
        "opinion_ru": "Human judgment / account rules — Reject as auto Earn.",
        "automation_officially_allowed": False,
        "has_api": False,
        "pays_providers": True,
        "no_forbidden_human_judgment": False,
        "evidence_status": "hard_reject",
        "hard_reject": True,
        "opportunity_id": None,
    },
    {
        "id": "platform-scale",
        "title": "Scale AI",
        "track": "reject",
        "first_payout_score": 0,
        "autonomy_score": 0,
        "opinion_ru": (
            "Не источник автоматического дохода Virtus (customer/requester path). "
            "Reject как Farm Earn."
        ),
        "automation_officially_allowed": False,
        "has_api": True,
        "pays_providers": False,
        "no_forbidden_human_judgment": False,
        "evidence_status": "hard_reject",
        "hard_reject": True,
        "opportunity_id": None,
    },
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bucket(platform: dict[str, Any]) -> str:
    """reject | research | go | commercial | paused"""
    stage = str(platform.get("pipeline_stage") or "")
    evidence = str(platform.get("evidence_status") or "")
    if platform.get("hard_reject") or stage in ("hard_reject", "reject_or_incomplete"):
        return "reject"
    if evidence == "paused_until_first_euro" or stage == "paused":
        return "paused"
    if platform.get("is_first_pick") or str(platform.get("track") or "") == "A":
        # Own API + Stripe — Commercial Engine, not «found on the internet»
        return "commercial"
    if stage in ("research_fit", "research_later") or evidence in (
        "research_hypothesis",
        "research_later",
    ):
        return "research"
    if stage == "first_connector_candidate":
        return "go"
    return "research"


def build_market_digest(
    *,
    platforms: list[dict[str, Any]],
    scanned_at: str | None = None,
) -> dict[str, Any]:
    """CEO daily digest — counts + honest empty Farm GO market."""
    buckets: dict[str, list[dict[str, Any]]] = {
        "reject": [],
        "research": [],
        "go": [],
        "commercial": [],
        "paused": [],
    }
    for p in platforms:
        b = _bucket(p)
        buckets.setdefault(b, []).append(
            {
                "id": p.get("id"),
                "title": p.get("title"),
                "pipeline_stage": p.get("pipeline_stage"),
                "opinion_ru": p.get("opinion_ru"),
                "earn_fit_ok": bool((p.get("earn_fit") or {}).get("ok")),
            }
        )

    farm_go = list(buckets["go"])
    # Suitable Farm Earn = GO from foreign markets (not Commercial Stripe path)
    suitable_farm = farm_go
    if suitable_farm:
        verdict_ru = (
            f"Найдена {len(suitable_farm)} площадка(и) к подключению Earn Connector — "
            "рекомендуется Legal Review + Owner Gate."
        )
        empty = False
    else:
        verdict_ru = (
            "Сегодня подходящих Earn-платформ (чужой оплачиваемый авто-рынок) не найдено. "
            "Это честный ответ Scanner, не поломка. "
            "Короткий путь к REAL — Commercial: Micro 5 € + Stripe."
        )
        empty = True

    n_reject = len(buckets["reject"])
    n_research = len(buckets["research"])
    n_go = len(suitable_farm)
    n_paused = len(buckets["paused"])
    n_commercial = len(buckets["commercial"])
    total = n_reject + n_research + n_go + n_paused + n_commercial

    return {
        "ok": True,
        "title_ru": "Farm Market Scanner · суточный монитор",
        "scanned_at": scanned_at or _utc_now(),
        "mission_ru": (
            "Ферма сама ищет новые легальные цифровые рынки, где разрешено "
            "автоматическое выполнение работы, и предлагает подключить их как Earn Connector."
        ),
        "two_projects_ru": {
            "commercial": "Places → Lead → Email → Stripe → REAL (работает при покупателе)",
            "farm": (
                "Интернет → Scanner → ToS/Automation/API → Earn Connector → "
                "задания → External Payout → REAL (блок в развитии)"
            ),
        },
        "counts": {
            "total": total,
            "reject": n_reject,
            "research": n_research,
            "go": n_go,
            "paused": n_paused,
            "commercial": n_commercial,
        },
        "summary_ru": (
            f"Проверено {total}: {n_reject} — Reject · {n_research} — Research · "
            f"{n_go} — GO · {n_paused} — Pause · {n_commercial} — Commercial"
        ),
        "verdict_ru": verdict_ru,
        "empty_farm_market": empty,
        "buckets": buckets,
        "ceo_actions_ru": (
            [
                "Провести Legal Review по GO-кандидатам",
                "Owner Gate: аккаунт / ToS / payouts вручную",
                "Не ждать REAL без External Payout ID",
            ]
            if suitable_farm
            else [
                "Продолжить Commercial NOW: /api-access → Micro 5 €",
                "Завтра снова Monitor (рынок мог измениться)",
                "При появлении новой площадки — register-platform (research passport)",
            ]
        ),
        "finance_reality_ru": (
            "Scanner не создаёт рынок и не рисует REAL. "
            "Сначала факты и подтверждённые выплаты (Finance Reality Law)."
        ),
        "cadence_ru": "Рекомендуемый ритм: раз в сутки (или Run Monitor вручную).",
    }


def run_market_monitor(
    memory_dir: Path | None = None,
    *,
    extra_platforms: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Scan known + research platforms → persist digest for CEO."""
    from swarm.farm_engine_v1 import scan_earn_platforms

    extras = list(_MONITOR_EXTRA) + list(extra_platforms or [])
    scan = scan_earn_platforms(extra=extras)
    digest = build_market_digest(platforms=list(scan.get("platforms") or []))
    digest["scan_counts"] = scan.get("counts")
    if memory_dir:
        path = Path(memory_dir) / DIGEST_FILE
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(digest, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            digest["persisted"] = True
            digest["path"] = path.name
        except OSError as exc:
            digest["persisted"] = False
            digest["persist_error"] = str(exc)
    else:
        digest["persisted"] = False
    return digest


def load_latest_digest(memory_dir: Path | None) -> dict[str, Any] | None:
    if not memory_dir:
        return None
    path = Path(memory_dir) / DIGEST_FILE
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None
